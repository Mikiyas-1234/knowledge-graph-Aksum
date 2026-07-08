# SPARQL / RDF Representation

`aksum_kg.ttl` is the same graph as the Neo4j/Kuzu deliverables, converted to Turtle RDF —
CIDOC-CRM's native representation. 14,839 triples: 130 entities, 491 asserted relationships
(each with a direct CRM-property triple *and* a full-provenance `crm:E13_Attribute_Assignment`
reification), and 1,205 candidate co-occurrences.

## Why a separate RDF file, not just "Neo4j but exported differently"

CIDOC-CRM is an RDF/OWL ontology. Modeling it as Neo4j node/relationship properties (as the
earlier deliverables do) is a reasonable pragmatic choice for querying, but it's an
approximation — real interoperability with other CRM-compliant datasets (Pelagios,
ResearchSpace, ARIADNEplus, national heritage registries) requires actual RDF and SPARQL. This
file is that.

## Modeling choices

- **Every asserted relationship is written twice, on purpose**: once as a direct triple using
  the real CRM property (e.g. `crm:P53_has_former_or_current_location`) for simple pattern
  queries, and once as a `crm:E13_Attribute_Assignment` resource carrying
  `source_document`/`source_locator`/`evidence_type`/`confidence` — this is CIDOC-CRM's own
  sanctioned mechanism for provenance-bearing claims, not an invented workaround.
- **Candidate (co-occurrence) edges are never written as `crm:` properties.** They get their
  own `exv:CoOccurrence` resource class instead, so no SPARQL query can accidentally treat a
  low-confidence co-mention as an ontological fact just by pattern-matching on `crm:`.

## Namespaces

```
crm:  http://www.cidoc-crm.org/cidoc-crm/          (the actual CIDOC-CRM ontology)
ex:   http://example.org/aksum-kg/entity/            (entity instances — replace with your own domain before publishing)
exr:  http://example.org/aksum-kg/assertion/         (reified assertion/co-occurrence resources)
exv:  http://example.org/aksum-kg/vocab/             (this project's own provenance vocabulary — not part of CRM)
```

**Before publishing**, replace `example.org` with a domain you control and mint permanent,
dereferenceable URIs if you want this to be a proper Linked Open Data node — right now `ex:`/
`exv:` are placeholders.

## Example queries

```sparql
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX ex:  <http://example.org/aksum-kg/entity/>
PREFIX exv: <http://example.org/aksum-kg/vocab/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

# Everything found at Aksum (direct triple — fast, no provenance)
SELECT ?thing ?label WHERE {
  ?thing crm:P7_took_place_at ex:place_aksum .
  ?thing rdfs:label ?label .
}

# Same question, WITH full provenance per claim
SELECT ?thingLabel ?sourceDoc ?locator ?confidence WHERE {
  ?assertion a crm:E13_Attribute_Assignment ;
             crm:P141_assigned ex:place_aksum ;
             crm:P140_assigned_attribute_to ?thing ;
             exv:sourceDocument ?sourceDoc ;
             exv:sourceLocator ?locator ;
             exv:confidence ?confidence .
  ?thing rdfs:label ?thingLabel .
}

# Candidate co-occurrences above a threshold (review queue only)
SELECT ?aLabel ?bLabel ?count WHERE {
  ?c a exv:CoOccurrence ;
     exv:entityA ?a ; exv:entityB ?b ; exv:coMentionCount ?count .
  ?a rdfs:label ?aLabel . ?b rdfs:label ?bLabel .
  FILTER(?count >= 4)
} ORDER BY DESC(?count)
```

## Running it

```bash
pip install rdflib
python3 rdf_convert.py     # regenerates aksum_kg.ttl from the CSVs
python3 sparql_validate.py # runs the example queries above and prints real results
```

To use with a real triplestore (GraphDB, Apache Jena Fuseki, Oxigraph, Blazegraph) instead of
rdflib's in-memory engine, just load `aksum_kg.ttl` directly — it's standard Turtle, no
rdflib-specific extensions used.

## Known issues found and fixed during validation (disclosed, not hidden)

1. An early duplicate-check query used `CONTAINS(LCASE(?label), "ksum")`, which matched "Maleke
   **Aksum**" as a false positive alongside the real "Aksum" node — a query-precision bug, not a
   data duplication bug. Fixed by requiring an exact label match.
2. An early radiocarbon query required `rdfs:comment` as a non-optional triple pattern, which
   silently excluded all 9 radiocarbon `E13_Attribute_Assignment` resources because their
   `notes` field is legitimately empty (notes were only populated for edges where the source
   text needed interpretive context, not for direct lab measurements). Fixed with `OPTIONAL`.

Both are captured in `sparql_validate.py` as-fixed; see this file's git history / the project
`CHANGELOG.md` for the before/after if you want to see the actual bug.
