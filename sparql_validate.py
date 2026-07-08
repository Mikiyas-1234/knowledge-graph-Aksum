from rdflib import Graph

g = Graph()
g.parse("aksum_kg.ttl", format="turtle")

PREFIXES = """
PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/>
PREFIX ex: <http://example.org/aksum-kg/entity/>
PREFIX exv: <http://example.org/aksum-kg/vocab/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""

def run(title, query):
    print(f"\n--- {title} ---")
    for row in g.query(PREFIXES + query):
        print(tuple(row))

run("Instances per CIDOC-CRM class", """
SELECT ?class (COUNT(?s) AS ?n) WHERE {
  ?s a ?class .
} GROUP BY ?class ORDER BY DESC(?n)
""")

run("Confirm single Aksum node (no Axum duplicate) — exact label match", """
SELECT ?s ?label WHERE {
  ?s a crm:E53_Place ; rdfs:label ?label .
  FILTER(LCASE(STR(?label)) = "aksum")
}
""")

run("Direct triples: what is FOUND_AT / located at Aksum", """
SELECT ?thing ?label WHERE {
  ?thing crm:P7_took_place_at ex:place_aksum .
  ?thing rdfs:label ?label .
}
""")

run("Who ruled Aksum, with full provenance via the E13 reification", """
SELECT ?rulerLabel ?sourceDoc ?locator ?confidence WHERE {
  ex:place_aksum crm:P14i_performed ?ruler .
  ?ruler rdfs:label ?rulerLabel .
  ?assertion a crm:E13_Attribute_Assignment ;
             crm:P140_assigned_attribute_to ex:place_aksum ;
             crm:P141_assigned ?ruler ;
             exv:sourceDocument ?sourceDoc ;
             exv:sourceLocator ?locator ;
             exv:confidence ?confidence .
}
""")

run("Radiocarbon measurements and their calibrated context", """
SELECT ?measurementLabel ?contextLabel ?notes WHERE {
  ?assertion a crm:E13_Attribute_Assignment ;
             exv:assignedRelationship "DATES_CONTEXT_AT" ;
             crm:P140_assigned_attribute_to ?measurement ;
             crm:P141_assigned ?context .
  ?measurement rdfs:label ?measurementLabel .
  ?context rdfs:label ?contextLabel .
  OPTIONAL { ?assertion rdfs:comment ?notes }
}
""")

run("Candidate co-occurrences with count >= 4 (review queue, NOT asserted facts)", """
SELECT ?aLabel ?bLabel ?count WHERE {
  ?c a exv:CoOccurrence ;
     exv:entityA ?a ; exv:entityB ?b ; exv:coMentionCount ?count .
  ?a rdfs:label ?aLabel . ?b rdfs:label ?bLabel .
  FILTER(?count >= 4)
} ORDER BY DESC(?count)
""")

run("Sanity check: candidate co-occurrences NEVER appear as crm: properties", """
SELECT (COUNT(?s) AS ?count) WHERE {
  ?s a exv:CoOccurrence .
  FILTER EXISTS { ?anything a crm:E13_Attribute_Assignment ; exv:assignedRelationship "CO_OCCURS_WITH" }
}
""")
