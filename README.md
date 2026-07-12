# Aksum Archaeological Knowledge Graph

A source-traceable knowledge graph of the Aksumite archaeological record (Ethiopia/Eritrea,
c. 1st–7th century CE), built from four excavation reports and modeled on CIDOC-CRM. Every
node and edge in this graph carries a citation back to a specific document and page/line —
the graph is designed to be checked, not just trusted.

## What this is

Most archaeological knowledge graphs are hard to audit: entities get merged or split silently,
relationships get asserted without a source, and "95% ontology compliance" numbers can't be
traced to anything concrete. This project takes the opposite approach — small, verifiable, and
explicit about its own gaps — and treats that as a feature, not a limitation to apologize for.

Two layers ship together:
- A hand-curated gold set (51 entities / 35 relationships), each traced by hand to a specific
  page of a source document.
- An automated Tier-1 NER/RE pass (gazetteer + regex, not a trained model) run over the full
  text of all four sources, validated against the gold set (94% recall) rather than presented
  as ground truth on its own.

## Repository contents

```
publication/
├── nodes.csv                    Entities: places, persons, periods, objects,
│                                 architectural features, radiocarbon measurements
├── asserted_edges.csv           Citable relationships — gold-curated facts +
│                                 automated matches on explicit relation language
│                                 ("found at", "dated to", "excavated by"...)
├── candidate_edges.csv          Same-sentence co-occurrences with no explicit relation
│                                 verb — review queue, NOT asserted facts
├── aksum_kg_publication.cypher  Neo4j import script (nodes + both edge tiers,
│                                 tagged with a `status` property for filtering)
├── methods_statement.md         Current-state data documentation: coverage,
│                                 confidence tiers, known limitations
├── CHANGELOG.md                 Build history, including bugs found and fixed
│                                 during development (kept separate from the
│                                 methods statement on purpose — see below)
├── CRM_glossary.md              Plain-language key for every CIDOC-CRM class/
│                                 property code used in the data
├── ner_pipeline.py              The extraction/entity-resolution script itself —
│                                 runnable and auditable line by line
├── load_kuzu.py                 Loads the CSVs into an embedded Kuzu database
│                                 (openCypher-compatible; useful for local testing
│                                 without a Neo4j server)
└── validate_queries.py          Example queries + the recall/duplication checks
                                  referenced in methods_statement.md
```

## Sources

| Source | Coverage |
|---|---|
| Phillipson, "Aksum and the Northern Horn of Africa" (*Archaeology International* 15, 2011–12) | Full text |
| Fattovich, Manzo & Bard 1998, "Meroe and Aksum" | Citation page only — article body unavailable in the source file used |
| Sernicola et al. 2019, *Newsletter di Archeologia CISA* 10 | Full text |
| Phillipson, *Archaeology at Aksum, Ethiopia 1993–7*, Vol. II | Partial — front matter/TOC + radiocarbon appendix read directly; ~10,000 lines of artefact/stratigraphic chapters not yet processed |

Coverage gaps are disclosed per-entity (see `confidence` and `notes` columns), not silently
padded over.

## Design choices worth knowing about

- **No confidence-field redundancy.** Earlier drafts of this graph had three overlapping trust
  signals per edge doing the job of one; this version keeps `evidence_type` (asserted vs.
  candidate) as the primary signal and drops fields that only restated it.
- **Asserted and candidate relationships are separate files**, not a single filterable column.
  71% of raw extracted edges were low-confidence co-occurrence guesses — keeping them in the same
  table as citable facts would make casual queries misleading by default.
- **Radiocarbon dates are reified as their own nodes** (lab number, material, BP age, both
  calibrated confidence ranges) rather than flattened onto a place/period attribute — this
  preserves the distinction between "this context contains this feature" and "this specific
  sample returned this specific date."
- **One node-ID scheme** regardless of extraction tier (`{type}_{slug}`, e.g. `place_aksum`,
  `person_ezana`) — provenance lives in a column, not the identifier.

## Known limitations

- This is Tier-1 NER (gazetteer + regex), not a trained/fine-tuned model — recall depends on
  the term lists in `ner_pipeline.py` and will miss anything outside them.
- No entity linking to external authorities (Getty TGN/AAT, Pleiades, Wikidata) yet — labels are
  internally resolved only.
- All current sources are academic excavation reports. No oral-tradition or community-informant
  source is represented; this graph should not be read as a complete account of Aksumite
  knowledge production, and any use of it should say so.
- One source (Fattovich, Manzo & Bard 1998) contributes no entities due to a document-conversion
  gap, not an extraction failure.

Full detail on all of the above is in `publication/methods_statement.md`; the record of what
broke and got fixed while building this is in `publication/CHANGELOG.md`, kept separate so the
methods statement stays readable as a current-state reference rather than a build diary.

## Using the data

**Neo4j:** run `publication/aksum_kg_publication.cypher` against a fresh database. Both edge
tiers load with a `status` property:

```cypher
MATCH (a)-[r {status:'asserted'}]->(b) RETURN a,r,b;        // citable relationships only
MATCH (a)-[r {status:'candidate'}]->(b)
  WHERE r.co_mention_count >= 3 RETURN a,r,b;               // review queue
```

**Kuzu (embedded, no server needed):**

```bash
pip install kuzu
python publication/load_kuzu.py
python publication/validate_queries.py
```

**Validation:**

```bash
python publication/validate_queries.py --strict   # exit 1 on any check failure
```

## Citation

If you use this dataset, please cite the four underlying excavation reports directly (full
references in `publication/methods_statement.md`) in addition to this repository, since the
value here is the graph structure and provenance tracking, not the underlying archaeological
research itself.

## License

CC-BY-4.0 for the derived graph data; check the original reports' own terms for anything
reproduced from them beyond fair-use citation.
