"""Graph backends with one interface: an in-memory one for tests, Neo4j for real use.

Every read takes `levels` (the caller's allowed access levels) and filters nodes AND
edges with it, so restricted records cannot leak through a neighbour lookup.
"""
from collections import defaultdict
from .schema import RELATIONSHIPS


class InMemoryGraph:
    def __init__(self, nodes, edges):
        self.nodes = dict(nodes)
        self.out = defaultdict(list)
        for e in edges:
            self.out[e["source"]].append(e)

    def find_nodes(self, text, levels, limit=10):
        from .resolution import normalise
        q = normalise(text)
        hits = []
        for n in self.nodes.values():
            if n["access_level"] not in levels:
                continue
            names = [n["label"], *[a for a in n.get("aliases", "").split(";") if a.strip()]]
            if any(q and q in normalise(x) for x in names):
                hits.append(n)
        return hits[:limit]

    def neighbours(self, node_id, levels):
        rows = []
        for e in self.out.get(node_id, []):
            tgt = self.nodes.get(e["target"])
            if tgt and e["access_level"] in levels and tgt["access_level"] in levels:
                rows.append((e, tgt))
        return rows


class Neo4jGraph:
    """Same interface over Neo4j. Needs `pip install neo4j`; not exercised by unit tests."""

    def __init__(self, uri, user, password):
        from neo4j import GraphDatabase
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def load(self, nodes, edges):
        with self._driver.session() as s:
            s.run("CREATE CONSTRAINT node_id IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE")
            s.run("UNWIND $rows AS r MERGE (n:Entity {id: r.id}) SET n += r", rows=list(nodes.values()))
            by_rel = defaultdict(list)
            for e in edges:
                by_rel[e["relationship"]].append(e)
            for rel, rows in by_rel.items():
                if rel not in RELATIONSHIPS:  # relationship types cannot be parameters: whitelist them
                    raise ValueError(f"unknown relationship {rel}")
                s.run(f"UNWIND $rows AS r MATCH (a:Entity {{id: r.source}}), (b:Entity {{id: r.target}}) "
                      f"MERGE (a)-[x:{rel}]->(b) SET x += r", rows=rows)

    def find_nodes(self, text, levels, limit=10):
        q = ("MATCH (n:Entity) WHERE n.access_level IN $levels AND "
             "(toLower(n.label) CONTAINS toLower($t) OR toLower(coalesce(n.aliases,'')) CONTAINS toLower($t)) "
             "RETURN n LIMIT $limit")
        with self._driver.session() as s:
            return [dict(r["n"]) for r in s.run(q, t=text, levels=sorted(levels), limit=limit)]

    def neighbours(self, node_id, levels):
        q = ("MATCH (a:Entity {id: $id})-[e]->(b:Entity) "
             "WHERE e.access_level IN $levels AND b.access_level IN $levels RETURN e, b")
        with self._driver.session() as s:
            return [(dict(r["e"]), dict(r["b"])) for r in s.run(q, id=node_id, levels=sorted(levels))]
