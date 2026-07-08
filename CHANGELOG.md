# Changelog

## v0.3 (publication) — this delivery
- Applied the clarity-vs-distraction review directly:
  - Removed `epistemic_provenance` from edges (was redundant with which pipeline tier produced the edge; kept on nodes, where it is an independent axis — source type of the entity itself).
  - Split edges into `asserted_edges.csv` (gold-curated + explicit relation-pattern matches) and `candidate_edges.csv` (same-sentence co-occurrence only) — physically separate files rather than a filterable column, so a naive query doesn't return 71% low-confidence noise by default.
  - Replaced the flat, uninformative `confidence: 0.35` constant on co-occurrence edges with a real signal: `co_mention_count`, the number of times that entity pair actually co-occurs across the corpus.
  - Normalized all node IDs to one semantic scheme (`{type}_{slugified_label}`, e.g. `place_aksum`, `person_ezana`) regardless of which pipeline tier created the node. Provenance tier now lives only in the `epistemic_provenance`/`notes` columns, not in the identifier.
  - Added `CRM_glossary.md` so class/property codes are self-documenting without this conversation as context.

## v0.2 — automated Tier-1 NER/RE scale-up
- Ran gazetteer + regex NER/RE over the full text of all four sources (11,582 lines / 1,727 sentences), not samples.
- Result: 130 nodes (51 gold + 79 automated), 1,696 edges pre-split.
- **Bug found and fixed:** bare mentions ("Ezana") failed to merge into gold nodes ("King Ezana") — a 0.92 similarity-ratio threshold penalized length mismatch. Fixed by adding a token-containment check. Verified by rerun: no duplicate Ezana/Kaleb nodes.
- **Bug found and fixed:** the four rock-shelter gold nodes (numbered generic features, e.g. "rock shelter #1") were invisible to a name-based gazetteer. Added a dedicated regex for numbered features (`rock shelter #\d+`, `tomb \d+`, `room \d+`, `trench [A-Z]+\d*`). Recovered shelter #1 as a connected node; shelters #2–4 remain correctly merged but edge-less, because their source sentences are coordinate-only and don't co-occur with another gazetteer term in the same sentence unit — a real limitation of sentence-level co-occurrence, not a resolution failure.
- Validation: 48/51 gold entities (94%) independently reconnected by the automated pass, checked programmatically.
- Verified zero Aksum/Axum duplication and zero stopword-contaminated entities (both checked against the specific failure modes found in the original project's code).

## v0.1 — hand-curated pilot
- 51 nodes / 35 edges, each hand-traced to a specific page in one of the four source documents.
- Fixed the Aksum/Axum duplication manually as a single resolved node.
- Reified radiocarbon dates as their own `E16_Measurement` nodes rather than flattening dates onto place nodes.
- Disclosed source coverage gaps explicitly (Fattovich/Manzo/Bard source is a citation-page stub only; the 10,671-line Phillipson volume was sampled, not read in full, at this stage).
