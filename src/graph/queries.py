"""
Deterministic Cypher queries - no LLM involved. These answer structural
questions directly from the graph, guaranteeing faithfulness.
"""
from src.graph.neo4j_client import get_driver


def find_unused_modules() -> list[dict]:
    """ModuleDefs with zero incoming CONSUMES edges."""
    query = """
    MATCH (m:ModuleDef)
    WHERE NOT ()-[:CONSUMES]->(m)
    RETURN m.id AS module_id, m.name AS module_name
    """
    driver = get_driver()
    with driver.session() as session:
        result = session.run(query)
        rows = [dict(r) for r in result]
    driver.close()
    return rows


def find_version_drift() -> list[dict]:
    """Modules consumed at more than one distinct version across repos."""
    query = """
    MATCH (r:Repo)-[c:CONSUMES]->(m:ModuleDef)
    WITH m, collect(DISTINCT c.version) AS versions, collect({repo: r.id, version: c.version}) AS usages
    WHERE size(versions) > 1
    RETURN m.id AS module_id, m.name AS module_name, versions, usages
    """
    driver = get_driver()
    with driver.session() as session:
        result = session.run(query)
        rows = [dict(r) for r in result]
    driver.close()
    return rows


def find_consumers_of(module_name: str) -> list[dict]:
    """Blast radius: which repos consume a given module, at what version."""
    query = """
    MATCH (r:Repo)-[c:CONSUMES]->(m:ModuleDef {name: $module_name})
    RETURN r.id AS repo_id, c.version AS version, c.call_name AS call_name
    """
    driver = get_driver()
    with driver.session() as session:
        result = session.run(query, module_name=module_name)
        rows = [dict(r) for r in result]
    driver.close()
    return rows