"""
Aksum KG -> RDF/SPARQL conversion.

Why this exists: CIDOC-CRM is natively an RDF/OWL ontology. Everything so far
(Neo4j, Kuzu) has been an APPROXIMATION of CRM inside a property-graph model
-- workable, but not what CRM was designed for, and not queryable by the
standard tools the heritage-data community actually uses (GraphDB,
ResearchSpace, Jena/Fuseki, Wikidata-style federation). This script produces
the real thing.

Modeling choices:
  1. Every entity becomes a proper crm:E-class instance with a stable URI.
  2. Every ASSERTED relationship gets TWO representations:
       a. a direct semantic triple using the actual CRM property
          (e.g. crm:P53_has_former_or_current_location) -- convenient for
          simple pattern queries.
       b. a reified crm:E13_Attribute_Assignment resource carrying full
          provenance (source document, locator, evidence type, confidence).
          This is CIDOC-CRM's own sanctioned mechanism for "who claims this,
          based on what, with what confidence" -- not an invented workaround.
  3. CANDIDATE (co-occurrence) edges are deliberately NOT written as CRM
     property triples, because they are not asserted relations -- writing
     them as crm:P-properties would misrepresent a raw co-mention signal as
     an ontological claim. They get their own ex:CoOccurrence resource class
     instead, so a SPARQL query can never accidentally treat a candidate as
     a fact.
"""
import csv, re
from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS, XSD

CRM = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
EX = Namespace("http://example.org/aksum-kg/entity/")
EXR = Namespace("http://example.org/aksum-kg/assertion/")
EXV = Namespace("http://example.org/aksum-kg/vocab/")

g = Graph()
g.bind("crm", CRM)
g.bind("ex", EX)
g.bind("exr", EXR)
g.bind("exv", EXV)

def clean_prop(raw):
    """Extract a usable CRM property local name from messy source strings
    like 'P4_has_time-span / P39i_was_measured_by' -> 'P4_has_time-span'."""
    if not raw:
        return None
    first = re.split(r'\s*/\s*', raw.strip())[0]
    first = first.replace("-", "_")  # CRM URIs use underscores, not hyphens
    if re.match(r'^P\d+[a-z]?_', first):
        return first
    return None

# ---------------- Load nodes ----------------
with open("nodes.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        subj = EX[row["id"]]
        cls = row["cidoc_class"].replace("-", "_") if row["cidoc_class"] else "E1_CRM_Entity"
        g.add((subj, RDF.type, CRM[cls]))
        g.add((subj, RDFS.label, Literal(row["label"], lang="en")))
        if row["category"]:
            g.add((subj, EXV.category, Literal(row["category"])))
        if row["source_document"]:
            g.add((subj, EXV.sourceDocument, Literal(row["source_document"])))
        if row["source_locator"]:
            g.add((subj, EXV.sourceLocator, Literal(row["source_locator"])))
        if row["epistemic_provenance"]:
            g.add((subj, EXV.epistemicProvenance, Literal(row["epistemic_provenance"])))
        if row["confidence"]:
            g.add((subj, EXV.confidence, Literal(float(row["confidence"]), datatype=XSD.double)))
        if row["notes"]:
            g.add((subj, RDFS.comment, Literal(row["notes"], lang="en")))

# ---------------- Load asserted edges: direct triple + E13 reification ----------------
assertion_counter = 0
with open("asserted_edges.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        subj = EX[row["source"]]
        obj = EX[row["target"]]
        prop_name = clean_prop(row["cidoc_property"])
        if prop_name:
            g.add((subj, CRM[prop_name], obj))
        else:
            # No parseable CRM property -- fall back to a generic, clearly
            # non-CRM predicate rather than silently inventing a P-number.
            g.add((subj, EXV.relatedTo, obj))

        assertion_counter += 1
        a_uri = EXR[f"assertion_{assertion_counter:04d}"]
        g.add((a_uri, RDF.type, CRM.E13_Attribute_Assignment))
        g.add((a_uri, CRM.P140_assigned_attribute_to, subj))
        g.add((a_uri, CRM.P141_assigned, obj))
        g.add((a_uri, EXV.assignedRelationship, Literal(row["relationship"])))
        if prop_name:
            g.add((a_uri, EXV.assignedProperty, Literal(prop_name)))
        g.add((a_uri, EXV.sourceDocument, Literal(row["source_document"])))
        g.add((a_uri, EXV.sourceLocator, Literal(row["source_locator"])))
        g.add((a_uri, EXV.evidenceType, Literal(row["evidence_type"])))
        if row["confidence"]:
            g.add((a_uri, EXV.confidence, Literal(float(row["confidence"]), datatype=XSD.double)))
        if row["notes"]:
            g.add((a_uri, RDFS.comment, Literal(row["notes"], lang="en")))

# ---------------- Load candidate edges: reified co-occurrence ONLY, no CRM property ----------------
cooc_counter = 0
with open("candidate_edges.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        cooc_counter += 1
        c_uri = EXR[f"cooccurrence_{cooc_counter:04d}"]
        g.add((c_uri, RDF.type, EXV.CoOccurrence))
        g.add((c_uri, EXV.entityA, EX[row["source"]]))
        g.add((c_uri, EXV.entityB, EX[row["target"]]))
        g.add((c_uri, EXV.coMentionCount, Literal(int(row["co_mention_count"]), datatype=XSD.integer)))
        g.add((c_uri, EXV.sourceDocument, Literal(row["source_document"])))
        g.add((c_uri, EXV.sourceLocator, Literal(row["source_locator"])))
        if row["notes"]:
            g.add((c_uri, RDFS.comment, Literal(row["notes"], lang="en")))

g.serialize(destination="aksum_kg.ttl", format="turtle")
print(f"Triples written: {len(g)}")
print(f"Asserted-edge reifications: {assertion_counter}")
print(f"Candidate co-occurrence resources: {cooc_counter}")
