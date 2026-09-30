"""Graph backends with one interface: an in-memory one for tests, Neo4j for real use.

Every read takes `levels` (the caller's allowed access levels) and filters nodes AND
edges with it, so restricted records cannot leak through a neighbour lookup.
"""
from collections import defaultdict
from .schema import RELATIONSHIPS


def search_names(node):
    """Normalised label and aliases joined by ';', the string Neo4j searches (see Neo4jGraph.find_nodes)."""
    from .resolution import normalise
    names = [node["label"], *[a for a in node.get("aliases", "").split(";") if a.strip()]]
    return ";".join(dict.fromkeys(x for x in (normalise(n) for n in names) if x))


def _edge_order(row):
    """Deterministic edge order (relationship, other node id, locator), shared by every backend."""
    edge, other = row
    return (edge["relationship"], other["id"], edge["source_locator"])


class InMemoryGraph:
    def __init__(self, nodes, edges):
        self.nodes = dict(nodes)
        self.out = defaultdict(list)
        self.inc = defaultdict(list)
        for e in edges:
            self.out[e["source"]].append(e)
            self.inc[e["target"]].append(e)

    def find_nodes(self, text, levels, limit=10):
        """Normalised name/alias match. Rank: exact match, then more connections, then id.

        The connection count makes a work held by many manuscripts outrank any single manuscript that
        shares its title, and the id tie-break makes the order identical in every backend.
        """
        from .resolution import normalise
        q = normalise(text)
        if not q:
            return []
        hits = []
        for n in self.nodes.values():
            if n["access_level"] not in levels:
                continue
            names = search_names(n).split(";")
            if q in names:
                hits.append((0, n))
            elif any(q in x for x in names):
                hits.append((1, n))
        hits.sort(key=lambda h: (h[0], -(len(self.out.get(h[1]["id"], [])) + len(self.inc.get(h[1]["id"], []))), h[1]["id"]))
        return [n for _, n in hits[:limit]]

    def neighbours(self, node_id, levels):
        rows = []
        for e in self.out.get(node_id, []):
            tgt = self.nodes.get(e["target"])
            if tgt and e["access_level"] in levels and tgt["access_level"] in levels:
                rows.append((e, tgt))
        return sorted(rows, key=_edge_order)


    def incoming(self, node_id, levels):
        """(edge, source_node) for edges pointing at node_id, e.g. the manuscripts that contain a work."""
        rows = []
        for e in self.inc.get(node_id, []):
            src = self.nodes.get(e["source"])
            if src and e["access_level"] in levels and src["access_level"] in levels:
                rows.append((e, src))
        return sorted(rows, key=_edge_order)


class Neo4jGraph:
    """Same interface over Neo4j. Needs `pip install neo4j`; not exercised by unit tests."""

    def __init__(self, uri, user, password):
        from neo4j import GraphDatabase
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def load(self, nodes, edges, batch=5000):
        """Idempotent (MERGE). Nodes also get their CIDOC class as a label, like aksum_kg_publication.cypher."""
        from .schema import CLASS_BY_TYPE
        allowed_classes = set(CLASS_BY_TYPE.values())
        with self._driver.session() as s:
            s.run("CREATE CONSTRAINT node_id IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE")
            by_class = defaultdict(list)
            for n in nodes.values():
                n["search_names"] = search_names(n)
                by_class[n["cidoc_class"]].append(n)
            for cls, rows in by_class.items():
                if cls not in allowed_classes:  # labels cannot be parameters: whitelist them
                    raise ValueError(f"unknown CIDOC class {cls}")
                for i in range(0, len(rows), batch):
                    s.run(f"UNWIND $rows AS r MERGE (n:Entity {{id: r.id}}) SET n += r SET n:`{cls}`", rows=rows[i:i + batch])
            by_rel = defaultdict(list)
            for e in edges:
                by_rel[e["relationship"]].append(e)
            for rel, rows in by_rel.items():
                if rel not in RELATIONSHIPS:  # relationship types cannot be parameters: whitelist them
                    raise ValueError(f"unknown relationship {rel}")
                for i in range(0, len(rows), batch):
                    s.run(f"UNWIND $rows AS r MATCH (a:Entity {{id: r.source}}), (b:Entity {{id: r.target}}) "
                          f"MERGE (a)-[x:{rel} {{source_document: r.source_document, source_locator: r.source_locator}}]->(b) "
                          f"SET x += r", rows=rows[i:i + batch])

    def close(self):
        self._driver.close()

    def count(self):
        with self._driver.session() as s:
            return (s.run("MATCH (n:Entity) RETURN count(n) AS c").single()["c"],
                    s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"])

    def find_nodes(self, text, levels, limit=10):
        """Same rule and ranking as InMemoryGraph.find_nodes."""
        from .resolution import normalise
        q = normalise(text)
        if not q:
            return []
        cypher = ("MATCH (n:Entity) WHERE n.access_level IN $levels AND n.search_names CONTAINS $q "
                  "WITH n, CASE WHEN (';' + n.search_names + ';') CONTAINS (';' + $q + ';') THEN 0 ELSE 1 END AS exact, "
                  "COUNT { (n)--() } AS degree RETURN n ORDER BY exact, degree DESC, n.id LIMIT $limit")
        with self._driver.session() as s:
            return [dict(r["n"]) for r in s.run(cypher, q=q, levels=sorted(levels), limit=limit)]

    def neighbours(self, node_id, levels):
        q = ("MATCH (a:Entity {id: $id})-[e]->(b:Entity) "
             "WHERE e.access_level IN $levels AND b.access_level IN $levels "
             "RETURN e, b ORDER BY type(e), b.id, e.source_locator")
        with self._driver.session() as s:
            return [(dict(r["e"]), dict(r["b"])) for r in s.run(q, id=node_id, levels=sorted(levels))]

    def incoming(self, node_id, levels):
        q = ("MATCH (a:Entity)-[e]->(b:Entity {id: $id}) "
             "WHERE e.access_level IN $levels AND a.access_level IN $levels "
             "RETURN e, a ORDER BY type(e), a.id, e.source_locator")
        with self._driver.session() as s:
            return [(dict(r["e"]), dict(r["a"])) for r in s.run(q, id=node_id, levels=sorted(levels))]
