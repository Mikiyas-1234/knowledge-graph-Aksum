"""Adapter for vHMML reading-room JSON records -> catalogue rows for ingest.build_graph.

Only fields whose meaning is certain are mapped. Anything else that carries data
(contributors, parts, genres...) is returned in `unmapped` for a human to review,
because guessing a scribe or a date from an unseen schema would put false claims in the graph.
"""
import json

HANDLED = {"id", "_unrecognised", "PURL", "rights", "processedBy", "shelfMark", "notes", "hmmlProjectNumber", "objectType",
           "accessRestriction", "viewableOnline", "downloadOption", "externalFacsimileUrls", "support",
           "rightToLeft", "imagesLocation", "label", "rightsText", "attribution", "iiifManifest", "iconName", "lastUpdateDisplay", "country", "city",
           "holdingInstitution", "repository", "collection", "captureDateDisplay", "surrogateFormat",
           "alternateSurrogates", "externalBibliographyUrls", "currentStatus"}
CHECK_IF_FILLED = ("extents", "genres", "subjects", "features", "objectContributors", "parts")


def _empty(v):
    return v in ("", None, [], {})


def to_catalogue_row(rec):
    """Returns (row, unmapped). `row` has no title/date unless the record had them."""
    repo = rec.get("repository") or {}
    repo_name = repo.get("name", "")
    # Some records (e.g. monastery collections) have no shelfmark; the HMML project number then identifies them.
    shelf = rec.get("shelfMark") or rec.get("hmmlProjectNumber", "")
    if not shelf:
        raise ValueError(f"vHMML record {rec.get('id')} has neither shelfMark nor hmmlProjectNumber")
    is_stub = "stub record" in (rec.get("notes") or "").lower()
    uris = [repo.get(k) for k in ("authorityUriLC", "authorityUriVIAF") if repo.get(k)]
    note_bits = [f"vHMML id {rec.get('id') or str(rec.get('PURL', '')).rsplit('/', 1)[-1]}", f"access: {rec.get('accessRestriction', '')}".strip(),
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
    if rec.get("iiifManifest"):
        row["extra_notes"] += f"; IIIF: {rec['iiifManifest']}"
    unmapped = {k: rec[k] for k in CHECK_IF_FILLED if not _empty(rec.get(k))}
    unmapped.update({k: v for k, v in rec.items() if k not in HANDLED and k not in CHECK_IF_FILLED and not _empty(v)})
    if rec.get("_unrecognised"):
        unmapped["_unrecognised"] = rec["_unrecognised"]
    return row, unmapped


_TEXT_KEYS = {
    "label": "label", "country": "country", "city": "city", "repository": "repository",
    "shelfmark": "shelfMark", "current status": "currentStatus", "notes": "notes",
    "hmml project number": "hmmlProjectNumber", "hmml proj. num.": "hmmlProjectNumber",
    "permalink": "PURL", "permanent link": "PURL", "iiif link": "iiifManifest",
    "rights link": "rights", "rights": "rightsText", "attribution": "attribution",
    "access restrictions": "accessRestriction", "processed by": "processedBy",
    "surrogate format": "surrogateFormat", "type of record": "objectType",
}


def parse_page_text(text):
    """Parse a record pasted from the vHMML web page ("KEY:value" or "Key<TAB>value" lines).

    Returns a dict shaped like the JSON record. Unrecognised keys are kept under `_unrecognised`.
    A trailing "VIAF" link label on a value is dropped. A line with no value stays empty.
    """
    rec, unknown = {}, {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        sep = "\t" if "\t" in line else (":" if ":" in line else None)
        if sep is None:
            continue
        key, _, val = line.partition(sep)
        key, val = key.strip().lower(), val.strip()
        if val.endswith(" VIAF"):
            val = val[:-5].strip()
        target = _TEXT_KEYS.get(key)
        if target is None:
            unknown[key] = val
        elif val:
            rec[target] = val
    if "repository" in rec:
        rec["repository"] = {"name": rec["repository"]}
    if unknown:
        rec["_unrecognised"] = unknown
    return rec


def load_file(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return [data] if isinstance(data, dict) else list(data)
