"""Adapter for vHMML reading-room JSON records -> catalogue rows for ingest.build_graph.

Only fields whose meaning is certain are mapped. Anything else that carries data
(contributors, parts, genres...) is returned in `unmapped` for a human to review,
because guessing a scribe or a date from an unseen schema would put false claims in the graph.
"""
import json

HANDLED = {"id", "PURL", "rights", "processedBy", "shelfMark", "notes", "hmmlProjectNumber", "objectType",
           "accessRestriction", "viewableOnline", "downloadOption", "externalFacsimileUrls", "support",
           "rightToLeft", "imagesLocation", "iconName", "lastUpdateDisplay", "country", "city",
           "holdingInstitution", "repository", "collection", "captureDateDisplay", "surrogateFormat",
           "alternateSurrogates", "externalBibliographyUrls", "currentStatus"}
CHECK_IF_FILLED = ("extents", "genres", "subjects", "features", "objectContributors", "parts")


def _empty(v):
    return v in ("", None, [], {})


def to_catalogue_row(rec):
    """Returns (row, unmapped). `row` has no title/date unless the record had them."""
    repo = rec.get("repository") or {}
    repo_name = repo.get("name", "")
    shelf = rec.get("shelfMark", "")
    if not shelf:
        raise ValueError(f"vHMML record {rec.get('id')} has no shelfMark")
    is_stub = "stub record" in (rec.get("notes") or "").lower()
    uris = [repo.get(k) for k in ("authorityUriLC", "authorityUriVIAF") if repo.get(k)]
    note_bits = [f"vHMML id {rec.get('id')}", f"access: {rec.get('accessRestriction', '')}".strip(),
                 f"rights: {rec.get('rights', '')}".strip(), f"status: {rec.get('currentStatus', '')}".strip()]
    row = {
        "shelfmark": f"{repo_name} {shelf}".strip(),
        "alt_titles": rec.get("hmmlProjectNumber", ""),
        "repository": repo_name,
        "repository_uri": "; ".join(uris),
        "material": rec.get("support", ""),
        "scan_uri": rec.get("PURL", ""),
        "source_document": "vHMML",
        "source_locator": rec.get("PURL", ""),
        "access_level": "public",
        "confidence": 0.5 if is_stub else 1.0,
        "epistemic_provenance": "catalogue_stub" if is_stub else "catalogue_record",
        "extra_notes": "; ".join(b for b in note_bits if not b.endswith(": ")),
    }
    unmapped = {k: rec[k] for k in CHECK_IF_FILLED if not _empty(rec.get(k))}
    unmapped.update({k: v for k, v in rec.items() if k not in HANDLED and k not in CHECK_IF_FILLED and not _empty(v)})
    return row, unmapped


def load_file(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return [data] if isinstance(data, dict) else list(data)
