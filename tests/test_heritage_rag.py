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


class BetaMasaheftTests(unittest.TestCase):
    TEI = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="WRONG" type="mss"><teiHeader><fileDesc>
<titleStmt><title>Test Gospels</title></titleStmt>
<sourceDesc><msDesc xml:id="ms">
 <msIdentifier><repository ref="INS9999TST"/><idno>Test 1</idno><altIdentifier><idno>Old 7</idno></altIdentifier></msIdentifier>
 <msContents><msItem xml:id="i1"><title ref="LIT0001Test"/><msItem xml:id="i1.1"><title ref="LIT0002Sub#part"/></msItem></msItem></msContents>
 <physDesc><objectDesc><supportDesc><support><material key="parchment"/></support></supportDesc></objectDesc>
  <bindingDesc><binding><decoNote><material key="leather"/></decoNote></binding></bindingDesc></physDesc>
 <history><origin><origPlace><placeName ref="LOC0001Test"/></origPlace>
   <origDate notBefore="1400" notAfter="1450-12-31"/><origDate/><origDate when="sometime"/></origin>
  <provenance><persName role="owner" ref="PRS0001Own"/></provenance></history>
 <additional><adminInfo/></additional>
 <msPart xml:id="p1"><history><origin><origDate notBefore="1200" notAfter="1300"/></origin></history></msPart>
 <msContents><summary><persName role="scribe" ref="PRS0002Scr"/><persName role="patron">Unlinked Name</persName>
  <persName role="scribe donor" ref="PRS0003Two"/></summary></msContents>
</msDesc></sourceDesc></fileDesc></teiHeader></TEI>"""

    def run_one(self, name="Dir/Test1.xml"):
        import xml.etree.ElementTree as ET
        from collections import Counter
        from heritage_rag import betamasaheft as bm
        nodes, edges, stats = {}, [], Counter()
        ok = bm.tei_to_graph(ET.fromstring(self.TEI), name, nodes, edges, stats)
        return ok, nodes, edges, stats

    def rels(self, edges):
        return sorted((e["relationship"], e["target"]) for e in edges)

    def test_mapping(self):
        ok, nodes, edges, stats = self.run_one()
        self.assertTrue(ok)
        self.assertEqual(self.rels(edges), sorted([
            ("HELD_AT", "place_ins9999tst"), ("PRODUCED_AT", "place_loc0001test"), ("MADE_OF", "material_parchment"),
            ("CONTAINS_TEXT", "text_lit0001test"), ("CONTAINS_TEXT", "text_lit0002sub"),
            ("DATED_TO", "period_1400_1450_ce"), ("COPIED_BY", "person_prs0002scr"), ("COPIED_BY", "person_prs0003two")]))

    def test_identity_comes_from_filename_not_xml_id(self):
        ok, nodes, edges, stats = self.run_one()
        self.assertIn("manuscript_test1", nodes)
        self.assertEqual(stats["xml_id_differs_from_filename"], 1)
        self.assertIn("Test 1", nodes["manuscript_test1"]["aliases"])
        self.assertIn("Old 7", nodes["manuscript_test1"]["aliases"])

    def test_binding_material_and_part_dates_are_not_attached(self):
        _, nodes, edges, stats = self.run_one()
        self.assertNotIn("material_leather", nodes)
        self.assertNotIn("period_1200_1300_ce", nodes)
        self.assertEqual(stats["part_dates_not_attached"], 1)

    def test_unmapped_things_are_counted_not_guessed(self):
        _, nodes, edges, stats = self.run_one()
        self.assertEqual(stats["role_not_mapped:owner"], 1)
        self.assertEqual(stats["role_not_mapped:donor"], 1)
        self.assertEqual(stats["patron_without_ref"], 1)
        self.assertEqual(stats["date_element_empty"], 1)
        self.assertEqual(stats["date_unreadable"], 1)
        self.assertNotIn("person_unlinked_name", nodes)

    def test_year_parsing(self):
        from heritage_rag.betamasaheft import _year
        self.assertEqual([_year(x) for x in ("0530", "1800-10", "1919-05-24", "17-18 century", "", None)],
                         [530, 1800, 1919, None, None, None])

    def test_duplicate_id_is_skipped(self):
        import xml.etree.ElementTree as ET
        from collections import Counter
        from heritage_rag import betamasaheft as bm
        nodes, edges, stats = {}, [], Counter()
        root = ET.fromstring(self.TEI)
        self.assertTrue(bm.tei_to_graph(root, "A/Test1.xml", nodes, edges, stats))
        self.assertFalse(bm.tei_to_graph(root, "B/Test1.xml", nodes, edges, stats))
        self.assertEqual(stats["duplicate_manuscript_id_skipped"], 1)

    def test_file_without_msdesc_is_skipped(self):
        import xml.etree.ElementTree as ET
        from collections import Counter
        from heritage_rag import betamasaheft as bm
        stats = Counter()
        root = ET.fromstring('<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader/></TEI>')
        self.assertFalse(bm.tei_to_graph(root, "X.xml", {}, [], stats))
        self.assertEqual(stats["skipped_no_msDesc"], 1)

    def test_graph_is_searchable_by_shelfmark_alias(self):
        _, nodes, edges, _ = self.run_one()
        g = InMemoryGraph(nodes, edges)
        self.assertEqual(g.find_nodes("old 7", allowed_levels("public"))[0]["id"], "manuscript_test1")


class BmNamesTests(unittest.TestCase):
    WORK = """<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader><fileDesc><titleStmt>
<title xml:lang="gez">አርባዕቱ፡ ወንገል፡</title><title>Four Gospels</title></titleStmt></fileDesc></teiHeader>
<text><body/></text></TEI>"""

    def write(self, d, name, xml):
        with open(os.path.join(d, name), "w", encoding="utf-8") as f:
            f.write(xml)

    def test_latin_title_is_label_and_geez_is_alias(self):
        from heritage_rag import bm_names
        with tempfile.TemporaryDirectory() as d:
            self.write(d, "LIT0001Gospel.xml", self.WORK)
            self.write(d, "PRS0001X.xml", self.WORK.replace("Four Gospels", "Placeholder record"))
            names = bm_names.load_names([d])
        self.assertEqual(names["LIT0001Gospel"][0], "Four Gospels")
        self.assertIn("አርባዕቱ፡ ወንገል፡", names["LIT0001Gospel"][1])
        self.assertNotIn("PRS0001X", names)  # placeholder, and its Geez title alone is not trusted as a name either

    def test_apply_names_relabels_keeps_id_and_adds_id_alias(self):
        from heritage_rag import bm_names
        nodes = {"text_lit0001gospel": {"id": "text_lit0001gospel", "label": "LIT0001Gospel", "category": "work",
                                        "aliases": "", "notes": "x"},
                 "text_lit9999none": {"id": "text_lit9999none", "label": "LIT9999None", "category": "work",
                                      "aliases": "", "notes": "x"}}
        n = bm_names.apply_names(nodes, {"LIT0001Gospel": ("Four Gospels", ["Tetraevangelium"])})
        self.assertEqual(n, 1)
        self.assertEqual(nodes["text_lit0001gospel"]["label"], "Four Gospels")
        self.assertEqual(nodes["text_lit0001gospel"]["aliases"], "LIT0001Gospel;Tetraevangelium")
        self.assertEqual(nodes["text_lit9999none"]["label"], "LIT9999None")

    def test_relabelled_node_is_found_by_name_and_by_id(self):
        from heritage_rag import bm_names
        nodes = {"text_lit0001gospel": {"id": "text_lit0001gospel", "label": "LIT0001Gospel", "category": "work",
                                        "aliases": "", "notes": "x", "access_level": "public"}}
        bm_names.apply_names(nodes, {"LIT0001Gospel": ("Four Gospels", [])})
        g = InMemoryGraph(nodes, [])
        self.assertEqual(len(g.find_nodes("four gospels", {"public"})), 1)
        self.assertEqual(len(g.find_nodes("LIT0001Gospel", {"public"})), 1)


class IncomingTests(unittest.TestCase):
    def graph(self):
        nodes = {"m1": {"id": "m1", "label": "MS One", "access_level": "public", "aliases": ""},
                 "m2": {"id": "m2", "label": "MS Two", "access_level": "restricted", "aliases": ""},
                 "m3": {"id": "m3", "label": "MS Three", "access_level": "public", "aliases": ""},
                 "w": {"id": "w", "label": "Four Gospels", "access_level": "public", "aliases": ""}}
        def e(src, lvl="public"):
            return {"source": src, "target": "w", "relationship": "CONTAINS_TEXT", "access_level": lvl,
                    "source_document": "D", "source_locator": src}
        return InMemoryGraph(nodes, [e("m1"), e("m2", "restricted"), e("m3")])

    def test_incoming_respects_access(self):
        g = self.graph()
        self.assertEqual({s["id"] for _, s in g.incoming("w", {"public"})}, {"m1", "m3"})
        self.assertEqual({s["id"] for _, s in g.incoming("w", {"public", "restricted"})}, {"m1", "m2", "m3"})

    def test_which_manuscripts_contain_a_work(self):
        g = self.graph()
        llm = lambda p: json.dumps({"terms": ["Four Gospels"], "domains": ["manuscript"]}) if p.startswith("Return JSON") else "ok"
        out = agent.answer(g, llm, "Which manuscripts contain the Four Gospels?")
        self.assertEqual(sorted(c[1] for c in out["citations"]), ["m1", "m3"])
        self.assertEqual(out["dropped"], 0)

    def test_cap_is_reported_not_silent(self):
        g = self.graph()
        ev, dropped = agent.retrieve(g, ["Four Gospels"], {"public"}, per_node=1)
        self.assertEqual((len(ev), dropped), (1, 1))


class RankingTests(unittest.TestCase):
    def test_exact_match_beats_partial_even_when_later(self):
        nodes = {f"p{i}": {"id": f"p{i}", "label": f"Gospels of Place {i}", "access_level": "public", "aliases": ""} for i in range(5)}
        nodes["w"] = {"id": "w", "label": "Gospels", "access_level": "public", "aliases": ""}
        g = InMemoryGraph(nodes, [])
        self.assertEqual(g.find_nodes("gospels", {"public"}, limit=2)[0]["id"], "w")


class CypherExportTests(unittest.TestCase):
    def test_string_escaping(self):
        from heritage_rag.export_cypher import cy_str
        self.assertEqual(cy_str("a'b"), "'a\\'b'")
        self.assertEqual(cy_str("back\\slash"), "'back\\\\slash'")
        self.assertEqual(cy_str("two\nlines\ttab"), "'two\\nlines\\ttab'")
        self.assertEqual(cy_str("\u12a0\u1263"), "'\u12a0\u1263'")  # Geez stays as-is

    def test_script_has_constraint_labels_and_citations(self):
        from heritage_rag import export_cypher as ex
        nodes, edges, _ = build()[:3]
        for n in nodes.values():
            n["confidence"] = float(n["confidence"])
        for e in edges:
            e["confidence"] = float(e["confidence"])
        text = "\n".join(ex.statements(nodes, edges, batch=2))
        self.assertIn("CREATE CONSTRAINT node_id", text)
        self.assertIn("SET n:`E84_Information_Carrier`", text)
        self.assertIn("MERGE (a)-[x:HELD_AT", text)
        self.assertIn("x.source_locator = r[", text)
        self.assertIn("toFloat(r[", text)
        self.assertIn(", 1.0,", text)

    def test_batching_splits_large_groups(self):
        from heritage_rag import export_cypher as ex
        nodes = {f"n{i}": {"id": f"n{i}", "label": f"L{i}", "cidoc_class": "E53_Place", "category": "c", "aliases": "",
                           "access_level": "public", "confidence": 1.0} for i in range(5)}
        stmts = [s for s in ex.statements(nodes, [], batch=2) if s.startswith("UNWIND")]
        self.assertEqual(len(stmts), 3)

    def test_rows_are_positional_lists_not_maps(self):
        from heritage_rag import export_cypher as ex
        row = ex.cy_row({"id": "a", "label": "it's"}, ["id", "label", "missing"])
        self.assertEqual(row, "['a', 'it\\'s', '']")

    def test_unknown_class_or_relationship_rejected(self):
        from heritage_rag import export_cypher as ex
        with self.assertRaises(ValueError):
            list(ex.statements({"a": {"id": "a", "label": "x", "cidoc_class": "Evil`) DETACH DELETE (n", "aliases": ""}}, []))
        with self.assertRaises(ValueError):
            list(ex.statements({}, [{"relationship": "X]->() DELETE", "source": "a", "target": "b"}]))


if __name__ == "__main__":
    unittest.main()
