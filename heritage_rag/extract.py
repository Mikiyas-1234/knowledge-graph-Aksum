"""LLM relation extraction with a grounding check.

A claim is kept only if its supporting quote appears verbatim in the page text.
Kept claims become *candidate* edges for expert review; nothing is asserted automatically.
"""
import json
import unicodedata

from .schema import CLASS_BY_TYPE, RELATIONSHIPS, EDGE_COLUMNS, make_id, PUBLIC

CANDIDATE_CONFIDENCE = 0.4


def _norm(text):
    return " ".join(unicodedata.normalize("NFC", text).split())


def _prompt(text):
    return ("Extract relations stated in the text. Return JSON {\"claims\": [{\"subject\": str, \"subject_type\": str, "
            "\"relation\": str, \"object\": str, \"object_type\": str, \"quote\": str}]}. "
            f"subject_type/object_type must be one of {sorted(CLASS_BY_TYPE)}; relation one of {sorted(RELATIONSHIPS)}. "
            "quote must be copied exactly from the text. Do not infer anything the text does not say.\n\nTEXT:\n" + text)


def extract_claims(llm, text):
    """Returns (accepted, rejected). rejected holds (claim, reason) so bad output can be audited."""
    try:
        claims = json.loads(llm(_prompt(text))).get("claims", [])
    except (ValueError, AttributeError):
        return [], [({}, "unparseable model output")]
    body = _norm(text)
    accepted, rejected = [], []
    for c in claims:
        if not isinstance(c, dict):
            rejected.append((c, "not an object"))
        elif c.get("relation") not in RELATIONSHIPS:
            rejected.append((c, "unknown relation"))
        elif c.get("subject_type") not in CLASS_BY_TYPE or c.get("object_type") not in CLASS_BY_TYPE:
            rejected.append((c, "unknown entity type"))
        elif not (c.get("subject") and c.get("object")):
            rejected.append((c, "missing entity"))
        elif not c.get("quote") or _norm(c["quote"]) not in body:
            rejected.append((c, "quote not found in text"))
        else:
            accepted.append(c)
    return accepted, rejected


def to_candidate_rows(claims, source_document, source_locator, access_level=PUBLIC):
    """Claims -> (nodes, edges) in repo CSV conventions, all flagged as candidates."""
    nodes, edges = {}, []
    for c in claims:
        ids = []
        for who, kind in ((c["subject"], c["subject_type"]), (c["object"], c["object_type"])):
            nid = make_id(kind, who)
            ids.append(nid)
            nodes.setdefault(nid, {
                "id": nid, "label": who, "cidoc_class": CLASS_BY_TYPE[kind], "category": kind,
                "source_document": source_document, "source_locator": source_locator,
                "epistemic_provenance": "llm_extraction", "confidence": CANDIDATE_CONFIDENCE,
                "notes": "awaiting expert review", "aliases": "", "access_level": access_level, "domain": "manuscript"})
        edges.append({"source": ids[0], "target": ids[1], "relationship": c["relation"],
                      "cidoc_property": RELATIONSHIPS[c["relation"]], "source_document": source_document,
                      "source_locator": source_locator, "evidence_type": "llm_extraction",
                      "confidence": CANDIDATE_CONFIDENCE, "notes": f'quote: {c["quote"]}', "access_level": access_level})
    return nodes, edges
