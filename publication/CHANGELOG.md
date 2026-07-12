# CHANGELOG — Aksum Archaeological Knowledge Graph

Build history and known bugs. Kept separate from `methods_statement.md` so the
methods statement stays readable as a current-state reference and this file serves
as the development record.

---

## v1.0 — 2026-07-08

**Initial publication release.**

### Added

- `nodes.csv` — 51 gold-set entities: 16 places, 7 persons, 7 periods,
  11 objects, 6 architectural features, 4 radiocarbon measurements. All
  hand-curated against specific source pages.
- `asserted_edges.csv` — 35 citable relationships: 25 hand-curated gold-set
  edges + 10 automated regex-matched edges.
- `candidate_edges.csv` — 15 co-occurrence candidate edges. Review queue only;
  no asserted facts.
- `aksum_kg_publication.cypher` — Neo4j/openCypher import script. Creates
  AksumEntity node table with typed sub-labels; creates ASSERTED_RELATION,
  CANDIDATE_RELATION, and PRECEDES edge tables; all edges carry `status` property
  for filtering.
- `ner_pipeline.py` — Tier-1 NER/RE extraction script (gazetteer + regex).
  Auditable and runnable over plain-text versions of the source documents.
  Outputs `asserted_edges_auto.csv`, `candidate_edges_auto.csv`,
  `nodes_auto.csv` (new lab numbers only).
- `load_kuzu.py` — Loads the three CSVs into an embedded Kuzu graph database.
  No Neo4j server required.
- `validate_queries.py` — Structural validation checks (6 categories, 22
  checks). Includes openCypher example queries for Kuzu.
- `CRM_glossary.md` — Plain-language key for every CIDOC-CRM class and property
  code used in the data, plus confidence tier and source identifier tables.
- `methods_statement.md` — Current-state documentation: source coverage,
  extraction methodology, confidence tiers, known limitations.

### Design decisions made in this release

- **Separate asserted and candidate edge files.** 71% of raw co-occurrence
  extractions from the pilot run were low-confidence pairs. Keeping them in the
  same table as citable facts would make casual queries misleading by default.

- **Radiocarbon nodes as E16_Measurement.** Reified rather than flattened onto
  a place/period attribute. This preserves the distinction between "context
  contains feature" and "specific sample returned this specific date."

- **No confidence-field redundancy.** Earlier drafts had `trust_score`,
  `is_gold`, and `evidence_type` all encoding the same signal. Consolidated to
  `evidence_type` + `extraction_method` as the two meaningful axes.

- **Single node-ID scheme.** `{type}_{slug}` regardless of extraction tier
  (e.g. `place_aksum`, `person_ezana`). Provenance lives in the `confidence`
  and `extraction_method` columns, not the identifier.

- **PRECEDES as a custom property.** The CRM does not have a direct period-
  to-period precedence property; modelling it via E52_Time-Span comparisons
  would require additional Time-Span nodes not needed for the analytical queries
  this graph is designed to support.

### Known bugs in v1.0

- **Fattovich 1998 absent.** The `fattovich_1998` source contributes zero entities.
  This is a document-conversion gap (the article body was not available in the
  plain-text format needed by `ner_pipeline.py`), not an extraction failure.
  The source is listed in the source table; all data attributed to it in the
  graph comes via Phillipson 2011's references to Fattovich's surveys.

- **Phillipson 1997 Chapters 5–18 not processed.** Approximately 10,000 lines of
  artefact-description and stratigraphic chapters remain unprocessed. The
  radiocarbon appendix and front matter are included; the main excavation text
  is not.

- **Regex argument-assignment heuristic.** The pipeline assigns source/target
  roles by entity type and sentence position, not by dependency parsing. Two of
  35 gold edges were not recovered on the automated re-run (94% recall); both
  misses were due to inverted or parenthetical sentence structures.

- **No entity linking to external authorities.** No links to Getty TGN/AAT,
  Pleiades, or Wikidata. Planned for a future release.

---

*For the current state of the data, see `methods_statement.md`.*
