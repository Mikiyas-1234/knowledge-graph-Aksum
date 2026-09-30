"""Backend parity test: InMemoryGraph and Neo4jGraph must answer the same lookups the same way.

Runs only when NEO4J_PASSWORD is set (optionally NEO4J_URI, NEO4J_USER). It writes nodes whose ids start
with `itest_` and deletes them afterwards, so it is safe to run against a database that holds real data.
"""
import os
import unittest

from heritage_rag.access import allowed_levels
from heritage_rag.store import InMemoryGraph, Neo4jGraph


def fixture():
    def node(i, label, cls, level="public", aliases=""):
        return {"id": f"itest_{i}", "label": label, "cidoc_class": cls, "category": "x", "source_document": "D",
                "source_locator": i, "epistemic_provenance": "t", "confidence": 1.0, "notes": "", "aliases": aliases,
                "access_level": level, "domain": "manuscript"}

    def edge(a, b, rel="CONTAINS_TEXT", level="public"):
        return {"source": f"itest_{a}", "target": f"itest_{b}", "relationship": rel, "cidoc_property": "P",
                "source_document": "D", "source_locator": f"{a}-{b}", "evidence_type": "t", "confidence": 1.0,
                "notes": "", "access_level": level}
    nodes = {n["id"]: n for n in [
        node("w", "ʾArbāʿtu wangel", "E73_Information_Object", aliases="Four Gospels;LIT0001"),
        node("m1", "Four Gospels", "E84_Information_Carrier"),
        node("m2", "Gospels of Somewhere", "E84_Information_Carrier"),
        node("m3", "Secret Book", "E84_Information_Carrier", level="restricted"),
        node("p", "ʾƎndā ʾAbbā Garimā", "E53_Place", aliases="እንዳ")]}
    edges = [edge("m1", "w"), edge("m2", "w"), edge("m3", "w", level="restricted"), edge("m1", "p", "HELD_AT")]
    return nodes, edges


@unittest.skipUnless(os.environ.get("NEO4J_PASSWORD"), "set NEO4J_PASSWORD to run against a real Neo4j")
class ParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.neo = Neo4jGraph(os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
                             os.environ.get("NEO4J_USER", "neo4j"), os.environ["NEO4J_PASSWORD"])
        nodes, edges = fixture()
        cls.mem = InMemoryGraph(nodes, edges)
        cls.neo.load({k: dict(v) for k, v in nodes.items()}, edges)

    @classmethod
    def tearDownClass(cls):
        with cls.neo._driver.session() as s:
            s.run("MATCH (n:Entity) WHERE n.id STARTS WITH 'itest_' DETACH DELETE n")
        cls.neo.close()

    def ids(self, nodes):
        return [n["id"] for n in nodes]

    def test_find_nodes_same_results_and_order(self):
        for level in ("public", "custodian"):
            lv = allowed_levels(level)
            for q in ("four gospels", "Enda Abba Garima", "እንዳ", "gospels", "LIT0001", "nothing"):
                with self.subTest(q=q, role=level):
                    m = [i for i in self.ids(self.mem.find_nodes(q, lv, limit=10**6)) if i.startswith("itest_")]
                    n = [i for i in self.ids(self.neo.find_nodes(q, lv, limit=10**6)) if i.startswith("itest_")]
                    self.assertEqual(m, n)  # same ids in the same order

    def test_neighbours_and_incoming_same_and_access_filtered(self):
        for level in ("public", "custodian"):
            lv = allowed_levels(level)
            with self.subTest(role=level):
                key = lambda rows: [(e["source_locator"], t["id"]) for e, t in rows]  # order matters: the agent caps per node
                self.assertEqual(key(self.mem.neighbours("itest_m1", lv)), key(self.neo.neighbours("itest_m1", lv)))
                self.assertEqual(key(self.mem.incoming("itest_w", lv)), key(self.neo.incoming("itest_w", lv)))
        self.assertNotIn("itest_m3", [s["id"] for _, s in self.neo.incoming("itest_w", allowed_levels("public"))])


if __name__ == "__main__":
    unittest.main()
