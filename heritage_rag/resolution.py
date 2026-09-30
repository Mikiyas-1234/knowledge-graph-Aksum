"""Name normalisation and entity-resolution candidates.

Exact normalised matches merge automatically. Near matches are only *proposed*
for expert review, never merged, because a wrong merge of two people or two
manuscripts corrupts every answer built on the node.
"""
import re
import unicodedata
from difflib import SequenceMatcher

_MODIFIERS = "ʿʾ‘’'`ʻʼ"


def normalise(name: str) -> str:
    """Lowercase, strip diacritics and transliteration marks, collapse spaces.

    Ge'ez script is kept (NFC) so it is never confused with Latin transliteration;
    linking the two forms is an alias decision, made by an expert.
    """
    text = unicodedata.normalize("NFKD", name)
    text = "".join(c for c in text if not unicodedata.combining(c) and c not in _MODIFIERS)
    text = unicodedata.normalize("NFC", text).lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def resolve(records, review_threshold=0.88):
    """records: dicts with 'id', 'label' and optional 'aliases' (semicolon separated).

    Returns (merged, review). `merged` maps a kept id to the ids folded into it
    (records sharing any normalised label or alias). `review` lists kept-id pairs whose
    labels are similar but not equal, for an expert to decide.
    """
    parent = {r["id"]: r["id"] for r in records}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    owner = {}
    for rec in records:
        names = [rec["label"], *[a for a in rec.get("aliases", "").split(";") if a.strip()]]
        for key in {normalise(n) for n in names} - {""}:
            if key in owner:
                a, b = find(owner[key]), find(rec["id"])
                if a != b:
                    keep, drop = sorted((a, b))
                    parent[drop] = keep
            else:
                owner[key] = rec["id"]
    merged = {}
    for rec in records:
        root = find(rec["id"])
        if root != rec["id"]:
            merged.setdefault(root, []).append(rec["id"])
    roots = sorted({find(r["id"]) for r in records})
    label = {r["id"]: normalise(r["label"]) for r in records}
    review = []
    for i, a in enumerate(roots):
        for b in roots[i + 1:]:
            ratio = SequenceMatcher(None, label[a], label[b]).ratio()
            if ratio >= review_threshold:
                review.append((a, b, round(ratio, 3)))
    return merged, review
