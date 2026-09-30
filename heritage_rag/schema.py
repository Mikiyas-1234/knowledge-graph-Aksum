"""Node/edge vocabulary for the manuscript domain, in the repo's CIDOC-CRM style."""
import re
import unicodedata

PUBLIC = "public"
RESTRICTED = "restricted"
ACCESS_LEVELS = (PUBLIC, RESTRICTED)

# New CRM classes, added beside those in CRM_glossary.md.
CLASS_BY_TYPE = {
    "manuscript": "E84_Information_Carrier",
    "text": "E73_Information_Object",
    "person": "E21_Person",
    "place": "E53_Place",
    "period": "E4_Period",
    "material": "E57_Material",
}

# relationship -> CIDOC property. Reuses DATED_TO, MADE_OF, LOCATED_AT from the glossary.
RELATIONSHIPS = {
    "CONTAINS_TEXT": "P128_carries",
    "COPIED_BY": "P14_carried_out_by",
    "COMMISSIONED_BY": "P17_was_motivated_by",
    "PRODUCED_AT": "P7_took_place_at",
    "HELD_AT": "P55_has_current_location",
    "DATED_TO": "P4_has_time-span",
    "MADE_OF": "P45_consists_of",
    "PRACTICE_CONTINUES_AS": "P130_shows_features_of",  # cross-domain, always starts as candidate
}

NODE_COLUMNS = ["id", "label", "cidoc_class", "category", "source_document", "source_locator",
                "epistemic_provenance", "confidence", "notes", "aliases", "access_level", "domain"]
EDGE_COLUMNS = ["source", "target", "relationship", "cidoc_property", "source_document",
                "source_locator", "evidence_type", "confidence", "notes", "access_level"]


def slugify(text: str) -> str:
    """ASCII slug used in ids. Ge'ez-only labels fall back to a hex code so ids stay unique."""
    norm = unicodedata.normalize("NFKD", text)
    ascii_part = "".join(c for c in norm if ord(c) < 128)
    slug = re.sub(r"[^a-z0-9]+", "_", ascii_part.lower()).strip("_")
    if slug:
        return slug
    return "u" + "".join(f"{ord(c):x}" for c in text.strip())[:24]


def make_id(node_type: str, label: str) -> str:
    return f"{node_type}_{slugify(label)}"
