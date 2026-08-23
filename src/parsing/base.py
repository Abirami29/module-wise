"""
Generic intermediate representation for parsed infra-as-code data.

Any future parser (dbt, Helm, k8s manifests, etc.) should output into these
same two shapes, so everything downstream (graph builder, Cypher queries,
router) stays parser-agnostic.
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Entity:
    id: str                      # stable unique id, e.g. "infra-modules:vpc-base"
    type: str                    # "repo" | "module_def" | "module_call" | "resource" | "variable"
    name: str
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class Edge:
    type: str                    # "defines" | "consumes" | "contains"
    source_id: str
    target_id: str
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedRepo:
    repo_name: str
    entities: list[Entity] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)

    def add_entity(self, entity: Entity) -> None:
        self.entities.append(entity)

    def add_edge(self, edge: Edge) -> None:
        self.edges.append(edge)