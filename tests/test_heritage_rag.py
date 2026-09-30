import json
import os
import tempfile
import unittest

from heritage_rag import agent, ingest
from heritage_rag.access import allowed_levels, generalise_place
from heritage_rag.resolution import normalise, resolve
from heritage_rag.schema import slugify, make_id
from heritage_rag.store import InMemoryGraph

CATALOGUE = os.path.join(os.path.dirname(__file__), "..", "heritage_rag", "data", "sample_catalogue.csv")


def build():
    nodes, edges, rejected = ingest.build_graph(ingest.read_catalogue(CATALOGUE))
    return nodes, edges, rejected, InMemoryGraph(nodes, edges)


class SchemaTests(unittest.TestCase):
    def test_slug_and_id(self):
        self.assertEqual(make_id("person", "Scribe Alpha"), "person_scribe_alpha")

    def test_geez_only_label_gets_unique_ids(self):
        a, b = slugify("ገዕዝ"), slugify("ከብሩ")
        self.assertNotEqual(a, b)
        self.assertTrue(a.startswith("u"))


class ResolutionTests(unittest.TestCase):
    def test_transliteration_marks_are_ignored(self):
        self.assertEqual(normalise("Gädlä ʿAbbä"), normalise("Gadla Abba"))

    def test_exact_variants_merge_and_near_ones_go_to_review(self):
        recs = [{"id": "a", "label": "Debre Alpha"}, {"id": "b", "label": "debre  alpha"},
                {"id": "c", "label": "Debre Alphas"}, {"id": "d", "label": "Other Place"}]
        merged, review = resolve(recs)
        self.assertEqual(merged, {"a": ["b"]})
        self.assertEqual([(x, y) for x, y, _ in review], [("a", "c")])

    def test_alias_merges(self):
        merged, _ = resolve([{"id": "a", "label": "One", "aliases": "Two"}, {"id": "b", "label": "Two"}])
        self.assertEqual(merged, {"a": ["b"]})


class IngestTests(unittest.TestCase):
    def test_rows_without_shelfmark_are_rejected_not_guessed(self):
        nodes, edges, rejected, _ = build()
        self.assertEqual(rejected, [(4, ["shelfmark"])])
        self.assertEqual(sum(1 for n in nodes.values() if n["category"] == "manuscript"), 3)

    def test_every_edge_carries_a_citation_and_crm_property(self):
        _, edges, _, _ = build()
        self.assertTrue(edges)
        for e in edges:
            self.assertTrue(e["source_document"] and e["source_locator"] and e["cidoc_property"])

    def test_restricted_record_marks_shared_nodes_restricted(self):
        nodes, _, _, _ = build()
        self.assertEqual(nodes["manuscript_test_ms_002"]["access_level"], "restricted")
        self.assertEqual(nodes["person_patron_beta"]["access_level"], "restricted")

    def test_write_graph_round_trip(self):
        nodes, edges, _, _ = build()
        with tempfile.TemporaryDirectory() as d:
            ingest.write_graph(nodes, edges, d)
            self.assertEqual(len(ingest.read_catalogue(f"{d}/manuscript_nodes.csv")), len(nodes))


class AccessTests(unittest.TestCase):
    def test_unknown_role_fails_closed(self):
        self.assertEqual(allowed_levels("nobody"), {"public"})

    def test_coordinates_removed_for_public(self):
        node = {"id": "p", "lat": 1.0, "lon": 2.0}
        self.assertNotIn("lat", generalise_place(node, {"public"}))
        self.assertIn("lat", generalise_place(node, {"public", "restricted"}))

    def test_restricted_manuscript_hidden_from_public_but_visible_to_custodian(self):
        _, _, _, g = build()
        self.assertEqual(g.find_nodes("TEST-MS-002", allowed_levels("public")), [])
        self.assertEqual(len(g.find_nodes("TEST-MS-002", allowed_levels("custodian"))), 1)

    def test_node_shared_with_a_restricted_record_is_hidden_from_public(self):
        # Conservative rule: a place used by any restricted manuscript is treated as restricted.
        _, _, _, g = build()
        self.assertEqual(g.find_nodes("Test Island Church", allowed_levels("public")), [])
        public_edges = {e["relationship"] for e, _ in g.neighbours("manuscript_test_ms_001", allowed_levels("public"))}
        self.assertNotIn("PRODUCED_AT", public_edges)
        custodian_edges = {e["relationship"] for e, _ in g.neighbours("manuscript_test_ms_001", allowed_levels("custodian"))}
        self.assertIn("PRODUCED_AT", custodian_edges)


class AgentTests(unittest.TestCase):
    def llm(self, prompt):
        if prompt.startswith("Return JSON"):
            return json.dumps({"terms": ["TEST-MS-001"], "domains": ["manuscript", "ethnography"]})
        return "stub answer"

    def test_answer_cites_sources_and_reports_gap(self):
        _, _, _, g = build()
        out = agent.answer(g, self.llm, "Who copied TEST-MS-001?")
        self.assertIn(("SYNTHETIC-FIXTURE", "row 1"), out["citations"])
        self.assertEqual(out["gaps"], ["ethnography"])

    def test_public_role_cannot_retrieve_restricted_manuscript(self):
        _, _, _, g = build()
        llm = lambda p: json.dumps({"terms": ["TEST-MS-002"], "domains": ["manuscript"]}) if p.startswith("Return JSON") else "x"
        out = agent.answer(g, llm, "Tell me about TEST-MS-002")
        self.assertEqual(out["citations"], [])
        out = agent.answer(g, llm, "Tell me about TEST-MS-002", role="custodian")
        self.assertTrue(out["citations"])

    def test_bad_planner_output_falls_back(self):
        p = agent.plan(lambda _: "not json", "question?")
        self.assertEqual(p, {"terms": ["question?"], "domains": ["manuscript"]})


class VhmmlTests(unittest.TestCase):
    """Synthetic record shaped like a vHMML stub (the real file is not committed: see vHMML terms)."""
    REC = {"id": 1, "PURL": "https://example.org/1", "rights": "https://example.org/terms", "shelfMark": "MS 1",
           "notes": "<p>This is a stub record with provisional metadata.</p>", "hmmlProjectNumber": "TEST 1",
           "accessRestriction": "Unregistered", "support": "", "currentStatus": "Unknown",
           "repository": {"id": 9, "name": "Test Archive", "authorityUriLC": "https://id.example/lc"},
           "extents": [], "genres": [], "objectContributors": [], "parts": []}

    def test_stub_is_low_confidence_and_nothing_is_invented(self):
        from heritage_rag import vhmml
        row, unmapped = vhmml.to_catalogue_row(self.REC)
        nodes, edges, rejected = ingest.build_graph([row])
        self.assertEqual(rejected, [])
        ms = nodes["manuscript_test_archive_ms_1"]
        self.assertEqual((ms["confidence"], ms["epistemic_provenance"]), (0.5, "catalogue_stub"))
        self.assertEqual({e["relationship"] for e in edges}, {"HELD_AT"})
        self.assertEqual(unmapped, {})
        self.assertIn("TEST 1", ms["aliases"])

    def test_filled_unknown_fields_are_reported_not_guessed(self):
        from heritage_rag import vhmml
        rec = dict(self.REC, objectContributors=[{"x": 1}], somethingNew="a")
        _, unmapped = vhmml.to_catalogue_row(rec)
        self.assertEqual(set(unmapped), {"objectContributors", "somethingNew"})

    def test_missing_shelfmark_raises(self):
        from heritage_rag import vhmml
        with self.assertRaises(ValueError):
            vhmml.to_catalogue_row({"id": 2})


class OcrTests(unittest.TestCase):
    def test_cer(self):
        from heritage_rag.ocr import cer
        self.assertEqual(cer("abcd", "abcd"), 0.0)
        self.assertEqual(cer("abcd", "abxd"), 0.25)
        self.assertEqual(cer("ሀሁ ሂ", "ሀሁ   ሂ"), 0.0)  # whitespace runs ignored
        with self.assertRaises(ValueError):
            cer("", "x")

    def test_ethiopic_ratio_flags_latin_output(self):
        from heritage_rag.ocr import ethiopic_ratio
        self.assertEqual(ethiopic_ratio("ሀሁሂ"), 1.0)
        self.assertEqual(ethiopic_ratio("abc"), 0.0)
        self.assertEqual(ethiopic_ratio("1234"), 0.0)

    def test_evaluate_sorts_worst_first(self):
        from heritage_rag.ocr import evaluate
        fake = {"p1": "abcd", "p2": "wxyz"}
        out = evaluate(lambda p: fake[p], [("p1", "abcd"), ("p2", "abcd")])
        self.assertEqual(out["pages"][0]["page"], "p2")
        self.assertEqual(out["mean_cer"], 0.5)

    def test_missing_binary_gives_clear_error(self):
        from heritage_rag.ocr import TesseractOcr
        with self.assertRaisesRegex(RuntimeError, "not installed"):
            TesseractOcr(binary="definitely-not-a-binary")("x.png")


class ExtractTests(unittest.TestCase):
    TEXT = "Scribe Alpha copied this book at Test Island Church in the year 1450."

    def llm(self, claims):
        return lambda _: json.dumps({"claims": claims})

    GOOD = {"subject": "Test Book", "subject_type": "manuscript", "relation": "COPIED_BY",
            "object": "Scribe Alpha", "object_type": "person", "quote": "Scribe Alpha copied this book"}

    def test_grounded_claim_becomes_candidate_edge(self):
        from heritage_rag import extract
        ok, bad = extract.extract_claims(self.llm([self.GOOD]), self.TEXT)
        self.assertEqual((len(ok), bad), (1, []))
        nodes, edges = extract.to_candidate_rows(ok, "TEST-DOC", "p.1")
        self.assertEqual(edges[0]["confidence"], 0.4)
        self.assertEqual(edges[0]["evidence_type"], "llm_extraction")
        self.assertIn("person_scribe_alpha", nodes)

    def test_invented_quote_is_rejected(self):
        from heritage_rag import extract
        fake = dict(self.GOOD, quote="Scribe Alpha was born in 1400")
        ok, bad = extract.extract_claims(self.llm([fake]), self.TEXT)
        self.assertEqual((ok, bad[0][1]), ([], "quote not found in text"))

    def test_unknown_relation_and_type_rejected(self):
        from heritage_rag import extract
        ok, bad = extract.extract_claims(self.llm([dict(self.GOOD, relation="LOVED_BY"),
                                                   dict(self.GOOD, object_type="alien")]), self.TEXT)
        self.assertEqual([r for _, r in bad], ["unknown relation", "unknown entity type"])

    def test_garbage_output_is_handled(self):
        from heritage_rag import extract
        ok, bad = extract.extract_claims(lambda _: "not json", self.TEXT)
        self.assertEqual((ok, bad[0][1]), ([], "unparseable model output"))


class VhmmlPageTextTests(unittest.TestCase):
    PAGE = """LABEL:GG 00041
COUNTRY:Ethiopia
CITY:Tegrāy Province
REPOSITORY:Gunda Gundē Monastery
HMML PROJECT NUMBER:GG 00041
RIGHTS LINK:https://www.vhmml.org/terms
PERMALINK:https://w3id.org/vhmml/readingRoom/view/500916
IIIF LINK:https://www.vhmml.org/image/manifest/500916
RIGHTS:
ATTRIBUTION:Provided by the Hill Museum & Manuscript Library
"""

    def test_page_text_without_shelfmark_loads_by_project_number(self):
        from heritage_rag import vhmml
        rec = vhmml.parse_page_text(self.PAGE)
        self.assertEqual(rec["repository"], {"name": "Gunda Gundē Monastery"})
        self.assertEqual(rec["iiifManifest"], "https://www.vhmml.org/image/manifest/500916")
        row, unmapped = vhmml.to_catalogue_row(rec)
        self.assertEqual(row["shelfmark"], "Gunda Gundē Monastery GG 00041")
        self.assertEqual(unmapped, {})
        self.assertIn("500916", row["extra_notes"])
        nodes, edges, rejected = ingest.build_graph([row])
        self.assertEqual(rejected, [])
        self.assertIn("place_gunda_gunde_monastery", nodes)
        self.assertEqual([e["relationship"] for e in edges], ["HELD_AT"])

    def test_tab_format_with_viaf_suffix(self):
        from heritage_rag import vhmml
        rec = vhmml.parse_page_text("Repository\tNational Archives VIAF\nShelfmark\tMS 362\nHMML Proj. Num.\tEMML 7385\nNotes\tThis is a stub record with provisional metadata.")
        self.assertEqual(rec["repository"]["name"], "National Archives")
        row, _ = vhmml.to_catalogue_row(rec)
        self.assertEqual(row["confidence"], 0.5)

    def test_unknown_page_keys_are_reported(self):
        from heritage_rag import vhmml
        rec = vhmml.parse_page_text("Shelfmark:MS 1\nMystery Field:xyz")
        _, unmapped = vhmml.to_catalogue_row(rec)
        self.assertEqual(unmapped, {"_unrecognised": {"mystery field": "xyz"}})


if __name__ == "__main__":
    unittest.main()
