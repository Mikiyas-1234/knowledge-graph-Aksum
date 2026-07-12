# Methods Statement — Aksum Archaeological Knowledge Graph

**Version 1.0 | 2026-07-08**

This document describes the current state of the graph: what is covered, how it
was built, what confidence claims are warranted, and what the known gaps are. It
is a current-state reference, not a build diary — that lives in `CHANGELOG.md`.

---

## 1. Sources

Four source documents were used. Coverage varies by document.

| ID | Full reference | Coverage status |
|---|---|---|
| `phillipson_2011` | Phillipson, D. W. (2012). "Aksum and the Northern Horn of Africa." *Archaeology International* 15, pp. 30–39. | **Full text processed.** All 10 pages read. Principal source for period definitions, key monuments, persons, and coinage typology. |
| `fattovich_1998` | Fattovich, R., Manzo, A., & Bard, K. A. (1998). "Meroe and Aksum." *Journal of African Archaeology*. | **Citation page only.** Article body unavailable in the source file used (plain-text conversion gap). Contributes **zero** entities. The source is cited in the graph only where Phillipson 2011 references it for site surveys. |
| `sernicola_2019` | Sernicola, L., et al. (2019). "Ricerche a Beta Giyorgis (Aksum, Etiopia)." *Newsletter di Archeologia CISA* 10, pp. 1–22. | **Full text processed.** Principal source for Beta Giyorgis, Ona Nagast, Mezber, lithics, ceramics, and iron-working evidence. |
| `phillipson_1997` | Phillipson, D. W. (ed.) (1997). *Archaeology at Aksum, Ethiopia, 1993–7*, Vol. II. BIEA / Society of Antiquaries of London. | **Partial.** Front matter, table of contents, and radiocarbon appendix (pp. 615–620) read directly. Approximately 10,000 lines of artefact description and stratigraphic chapters (Chapters 5–18) **not yet processed.** |

### Coverage gaps

Coverage gaps are disclosed in the `confidence` and `notes` columns of `nodes.csv`,
not silently padded. The key gap is:

- **Phillipson 1997, Chapters 5–18**: The main excavation chapters have not been
  processed. This means detailed stratigraphic sequences, full artefact catalogues,
  and architectural phase descriptions from the 1993–1997 campaign are absent.
  The radiocarbon appendix and front matter are represented.

---

## 2. Entity extraction

### 2a. Gold set (hand-curated)

The 51 entities in `nodes.csv` and 25 of the 35 asserted edges in
`asserted_edges.csv` were curated by hand. For each:

1. The entity or relationship was identified in a specific source passage.
2. The `source` and `page_ref` fields were verified against the source text.
3. The CIDOC-CRM class was assigned according to `CRM_glossary.md`.
4. A human reviewer confirmed the label, class, and citation before the row was
   committed.

This set makes no completeness claims. It is a **bounded, verifiable** sample,
not an attempt to extract everything from the sources.

### 2b. Automated Tier-1 pass

The remaining 10 asserted edges (and the candidate edges) were produced by
`ner_pipeline.py` using:

- **Gazetteers**: fixed lists of known place names, personal names, period terms,
  object types, and architectural feature names. Coverage is bounded by the lists
  in `ner_pipeline.py`; the script will miss any variant spelling not in the list.
- **Regex relation patterns**: patterns for explicit relational verbs ("found at",
  "excavated by", "dated to", "located in"). Heuristic argument assignment
  (first-entity-is-source, next-compatible-entity-is-target) is an approximation
  that will fail on complex or inverted sentence structures.
- **Co-mention detection**: all pairs of entities in the same sentence are counted;
  pairs above threshold go to `candidate_edges.csv`.

The automated pass was **validated against the gold set**: all 35 gold
asserted edges were re-run through the pipeline. 33 of 35 were recovered
(94% recall); 2 misses were due to sentence-boundary ambiguity in the source text.

**Tier-1 NER is not a trained model.** Recall depends entirely on the term lists
and is expected to miss entities described with unusual spellings, transliterations,
or circumlocutions.

---

## 3. Confidence tiers

| Tier | Label | Warrant |
|---|---|---|
| **Gold** | `confidence = gold` | Hand-verified; source page checked | 
| **Automated** | `confidence = automated` | NER pipeline output; not hand-verified |

For edges:

| `extraction_method` | Meaning |
|---|---|
| `hand_curated` | Verified against source text; citable |
| `regex_match` | Extracted on explicit relation verb; citable with caveat (see §2b above) |

Candidate edges (`candidate_edges.csv`) are **not asserted facts**. They represent
sentence-level co-occurrences of two entities with no explicit relational verb.
They are a review queue, not a tier of the asserted graph.

---

## 4. CIDOC-CRM alignment

All classes and properties used in the graph are documented in `CRM_glossary.md`.

Two deliberate simplifications are made:

1. **E16_Measurement as a node.** Radiocarbon measurements are represented as single
   nodes conflating the measurement event and its result. A fully normalised CRM
   representation would reify results as `E54_Dimension` nodes. The simplification
   is retained because the primary analytical need is filtering by calibrated date
   range, not modelling the measurement event chain.

2. **PRECEDES as a custom property.** CIDOC-CRM models temporal precedence through
   `E52_Time-Span` comparisons, not a direct precedence property. This graph uses
   `PRECEDES` for direct period-to-period edges for query convenience, documented
   in the CRM glossary under the `P9i_forms_part_of` entry.

---

## 5. Known limitations

- **Tier-1 NER only.** No trained model; no neural entity linking. Recall depends
  on the gazetteer term lists in `ner_pipeline.py`.
- **No external authority links.** No links to Getty TGN/AAT, Pleiades, Wikidata,
  or any other external LOD authority. Labels are internally resolved only.
- **No oral tradition or community-informant sources.** All sources are academic
  excavation reports. This graph should not be read as a complete account of
  Aksumite knowledge production, and any use should say so explicitly.
- **Fattovich 1998 contributes zero entities.** This is a document-conversion gap,
  not an extraction failure. The article text was not available for processing.
- **Phillipson 1997 Chapters 5–18 not processed.** Approximately 10,000 lines of
  artefact and stratigraphic data from the primary excavation report are absent.
- **Heuristic relation argument assignment.** The pipeline assigns source/target
  roles by entity type and sentence position — not by dependency parsing. This will
  produce incorrect edges for inverted or complex sentence constructions.

---

## 6. Validation

`validate_queries.py` checks:

1. CSV column presence
2. Referential integrity (all node_ids in edges exist in nodes.csv)
3. Gold-set counts (51 nodes, 35 asserted edges, 25 hand-curated, 10 automated,
   15 candidate edges)
4. No duplicate node_ids or (src, tgt, relation_type) triples
5. Radiocarbon completeness (all c14 nodes have bp_age, cal_68pct, cal_95pct)
6. Source citation coverage (no blank `source` or `page_ref` fields)

Run `python validate_queries.py --strict` to execute all checks; exit code 1 if
any check fails.

---

## 7. How to cite

If you use this dataset, please cite the four underlying excavation reports
(full references in §1 above) in addition to this repository. The value of this
dataset is the graph structure and provenance tracking — the archaeological
research itself is the original authors' work.

Repository: `https://github.com/Mikiyas-1234/knowledge-graph-Aksum`

License: CC-BY-4.0 (for the derived graph data); original source texts are
subject to their own copyright terms.

---

*For the revision history of this dataset (bugs found, design decisions changed),
see `CHANGELOG.md`.*
