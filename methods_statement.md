# Data & Methods Statement — Aksum Archaeological Knowledge Graph (v0.3, publication)

Build history and bug-fix narrative are in `CHANGELOG.md`. This document states only what the
current dataset *is*, not how it got here.

## 1. Contents

| File | What it is | Trust level |
|---|---|---|
| `nodes.csv` | 130 entities (places, persons, periods, objects, features, measurements) | See `epistemic_provenance`/`confidence` per row |
| `asserted_edges.csv` | 491 relationships — hand-curated gold facts + automated matches on explicit relation language ("found at," "dated to," "excavated by," "made of," "located at") | Treat as claims: check `evidence_type` and `notes` before citing |
| `candidate_edges.csv` | 1,205 same-sentence co-occurrences with no explicit relation verb | Treat as leads for human review, not facts. `co_mention_count` indicates how often the pair recurs across the corpus. |
| `CRM_glossary.md` | Plain-language key for every CIDOC-CRM class/property code used | Reference |
| `aksum_kg_publication.cypher` | Ready-to-run Neo4j import (nodes + both edge sets, tagged by a `status` property) | — |

## 2. Source coverage

| Source | Coverage |
|---|---|
| S1 — Phillipson, "Aksum and the Northern Horn of Africa" (2011–12) | Full text |
| S2 — Fattovich, Manzo & Bard 1998 | Citation/cover page only — the article body was not present in the converted file supplied. No entities are drawn from body text that doesn't exist in this dataset's source material. |
| S3 — Sernicola et al. 2019 | Full text |
| S4 — Phillipson, *Archaeology at Aksum 1993–7* Vol. II | Front matter/TOC + Appendix VI (radiocarbon dates) read directly and in full; the remaining ~10,000 lines (artefact chapters, stratigraphic narrative) have not yet been processed. Entities drawn only from the table of contents (e.g. Tomb of Bazen) carry `confidence: 0.9` and a note stating the body chapter is unprocessed. |

## 3. Known limitations

1. S4 coverage is partial (see above) — this graph does not yet support comprehensive claims about the full 1993–7 excavation.
2. S2 contributes no entities, due to a source-conversion gap rather than an extraction failure.
3. `candidate_edges.csv` entities were extracted by gazetteer + regex matching (not a trained NER model); recall is limited to terms in the current gazetteer lists, documented in `ner_pipeline.py`.
4. No entity linking to external authority files (Getty TGN/AAT, Pleiades, Wikidata) has been performed yet — labels are internally resolved only.
5. All current sources are `academic_excavation_report`. No oral-tradition or community-informant source is yet represented; any resulting publication should state this as a limitation rather than let the graph imply completeness.

## 4. How to use the two edge files together in Neo4j

Both are loaded with a `status` property (`asserted` / `candidate`) so they can be queried
together or filtered independently:

```cypher
// Only asserted, citable relationships
MATCH (a)-[r {status:'asserted'}]->(b) RETURN a,r,b;

// Candidate relationships for human review, above a co-mention threshold
MATCH (a)-[r {status:'candidate'}]->(b) WHERE r.co_mention_count >= 3 RETURN a,r,b;
```
