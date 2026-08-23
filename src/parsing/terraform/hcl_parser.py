"""
Parses Terraform HCL files into the generic Entity/Edge shape (base.py).

Handles two repo shapes:
  1. A "module registry" repo (has a modules/<name>/ subfolder per module) ->
     produces module_def entities + resource entities + "defines" edges.
  2. A "consumer" repo (has module blocks referencing an external source) ->
     produces module_call entities + "consumes" edges, with version pulled
     from the ?ref= query param in the source URL.
"""
import re
from pathlib import Path

import hcl2

from src.parsing.base import Entity, Edge, ParsedRepo

# Matches: git::https://.../infra-modules.git//modules/vpc-base?ref=v2.0.0
# Captures module name ("vpc-base") and ref ("v2.0.0")
MODULE_SOURCE_RE = re.compile(r"//modules/([^/?]+)(?:\?ref=([^&\s\"]+))?")


def _load_tf_file(path: Path) -> dict:
    with open(path, "r") as f:
        return hcl2.load(f)


def parse_module_registry_repo(repo_path: Path, repo_name: str) -> ParsedRepo:
    """Parse a repo like infra-modules: modules/<name>/*.tf defines each module."""
    parsed = ParsedRepo(repo_name=repo_name)
    repo_entity = Entity(id=repo_name, type="repo", name=repo_name)
    parsed.add_entity(repo_entity)

    modules_dir = repo_path / "modules"
    if not modules_dir.exists():
        return parsed

    for module_dir in sorted(p for p in modules_dir.iterdir() if p.is_dir()):
        module_name = module_dir.name
        module_id = f"{repo_name}:{module_name}"

        resources: list[dict] = []
        variables: list[dict] = []

        for tf_file in module_dir.glob("*.tf"):
            try:
                data = _load_tf_file(tf_file)
            except Exception as e:
                print(f"  [warn] failed to parse {tf_file}: {e}")
                continue

            for block in data.get("resource", []):
                for res_type, res_bodies in block.items():
                    for res_name in res_bodies:
                        resources.append({"type": res_type, "name": res_name})

            for block in data.get("variable", []):
                for var_name, var_body in block.items():
                    variables.append({
                        "name": var_name,
                        "default": var_body.get("default"),
                        "description": var_body.get("description"),
                    })

        module_entity = Entity(
            id=module_id,
            type="module_def",
            name=module_name,
            properties={
                "resource_count": len(resources),
                "resource_types": sorted({r["type"] for r in resources}),
                "variables": [v["name"] for v in variables],
            },
        )
        parsed.add_entity(module_entity)
        parsed.add_edge(Edge(type="defines", source_id=repo_name, target_id=module_id))

    return parsed


def parse_consumer_repo(repo_path: Path, repo_name: str) -> ParsedRepo:
    """Parse a repo like service-webshop: module blocks consuming external modules."""
    parsed = ParsedRepo(repo_name=repo_name)
    repo_entity = Entity(id=repo_name, type="repo", name=repo_name)
    parsed.add_entity(repo_entity)

    for tf_file in repo_path.glob("*.tf"):
        try:
            data = _load_tf_file(tf_file)
        except Exception as e:
            print(f"  [warn] failed to parse {tf_file}: {e}")
            continue

        for block in data.get("module", []):
            for call_name, call_body in block.items():
                source = call_body.get("source", "")
                match = MODULE_SOURCE_RE.search(source)
                if not match:
                    print(f"  [warn] could not parse source: {source}")
                    continue

                module_name, ref = match.group(1), match.group(2) or "unknown"
                call_id = f"{repo_name}:{call_name}"
                # target_id points at the module_def id from the registry repo.
                # Assumes the registry repo is named "infra-modules" - adjust if renamed.
                target_module_id = f"infra-modules:{module_name}"

                call_entity = Entity(
                    id=call_id,
                    type="module_call",
                    name=call_name,
                    properties={"module_name": module_name, "version": ref},
                )
                parsed.add_entity(call_entity)
                parsed.add_edge(Edge(
                    type="consumes",
                    source_id=repo_name,
                    target_id=target_module_id,
                    properties={"version": ref, "call_name": call_name},
                ))

    return parsed


def parse_repo(repo_path: Path) -> ParsedRepo:
    """Auto-detect repo shape and parse accordingly."""
    repo_name = repo_path.name
    if (repo_path / "modules").exists():
        return parse_module_registry_repo(repo_path, repo_name)
    return parse_consumer_repo(repo_path, repo_name)