"""
Loads ParsedRepo objects (from Epic 2's parser) into Neo4j.

Node labels: Repo, ModuleDef, ModuleCall
Edge types: DEFINES, CONSUMES

Idempotent: safe to re-run (used by clear_graph + Story 8.3's rebuild button).
"""
from pathlib import Path

from src.graph.neo4j_client import get_driver
from src.parsing.terraform.hcl_parser import parse_repo
from src.parsing.base import ParsedRepo

DATA_DIR = Path("data/github-repos")


def clear_graph(driver):
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    print("Graph cleared")


def load_parsed_repo(driver, parsed: ParsedRepo):
    with driver.session() as session:
        for entity in parsed.entities:
            if entity.type == "repo":
                session.run(
                    "MERGE (r:Repo {id: $id}) SET r.name = $name",
                    id=entity.id, name=entity.name,
                )
            elif entity.type == "module_def":
                session.run(
                    """
                    MERGE (m:ModuleDef {id: $id})
                    SET m.name = $name,
                        m.resource_count = $resource_count,
                        m.resource_types = $resource_types,
                        m.variables = $variables
                    """,
                    id=entity.id, name=entity.name,
                    resource_count=entity.properties.get("resource_count", 0),
                    resource_types=entity.properties.get("resource_types", []),
                    variables=entity.properties.get("variables", []),
                )
            elif entity.type == "module_call":
                session.run(
                    """
                    MERGE (c:ModuleCall {id: $id})
                    SET c.name = $name,
                        c.module_name = $module_name,
                        c.version = $version
                    """,
                    id=entity.id, name=entity.name,
                    module_name=entity.properties.get("module_name"),
                    version=entity.properties.get("version"),
                )

        for edge in parsed.edges:
            if edge.type == "defines":
                session.run(
                    """
                    MATCH (r:Repo {id: $source_id}), (m:ModuleDef {id: $target_id})
                    MERGE (r)-[:DEFINES]->(m)
                    """,
                    source_id=edge.source_id, target_id=edge.target_id,
                )
            elif edge.type == "consumes":
                # target_id points at a ModuleDef in infra-modules (e.g. "infra-modules:vpc-base")
                session.run(
                    """
                    MATCH (r:Repo {id: $source_id}), (m:ModuleDef {id: $target_id})
                    MERGE (r)-[c:CONSUMES {version: $version, call_name: $call_name}]->(m)
                    """,
                    source_id=edge.source_id, target_id=edge.target_id,
                    version=edge.properties.get("version"),
                    call_name=edge.properties.get("call_name"),
                )


def build_full_graph(clear_first: bool = True):
    driver = get_driver()
    if clear_first:
        clear_graph(driver)

    for repo_path in sorted(p for p in DATA_DIR.iterdir() if p.is_dir()):
        print(f"Loading {repo_path.name} into graph...")
        parsed = parse_repo(repo_path)
        load_parsed_repo(driver, parsed)

    driver.close()
    print("Graph build complete.")


if __name__ == "__main__":
    build_full_graph()