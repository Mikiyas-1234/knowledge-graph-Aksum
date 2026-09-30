"""Manuscript catalogue rows -> nodes/edges in the repo's CSV conventions."""
import csv
from .schema import CLASS_BY_TYPE, RELATIONSHIPS, NODE_COLUMNS, EDGE_COLUMNS, make_id, PUBLIC, ACCESS_LEVELS

REQUIRED = ("shelfmark", "source_document", "source_locator")


def _node(nodes, node_type, label, row, category, aliases="", notes=""):
    nid = make_id(node_type, label)
    if nid not in nodes:
        nodes[nid] = {
            "id": nid, "label": label, "cidoc_class": CLASS_BY_TYPE[node_type], "category": category,
            "source_document": row["source_document"], "source_locator": row["source_locator"],
            "epistemic_provenance": "catalogue_record", "confidence": 1.0, "notes": notes,
            "aliases": aliases, "access_level": row["access_level"], "domain": "manuscript",
        }
    elif row["access_level"] != PUBLIC:
        # A node touched by any restricted record stays restricted.
        nodes[nid]["access_level"] = row["access_level"]
    return nid


def _edge(edges, src, tgt, rel, row, evidence="catalogue_record"):
    edges.append({
        "source": src, "target": tgt, "relationship": rel, "cidoc_property": RELATIONSHIPS[rel],
        "source_document": row["source_document"], "source_locator": row["source_locator"],
        "evidence_type": evidence, "confidence": 1.0, "notes": "", "access_level": row["access_level"],
    })


def build_graph(rows):
    """Returns (nodes, edges). Rows missing a citation are rejected, not guessed."""
    nodes, edges, rejected = {}, [], []
    for i, raw in enumerate(rows, start=1):
        row = {k: (v or "").strip() for k, v in raw.items()}
        missing = [c for c in REQUIRED if not row.get(c)]
        row["access_level"] = row.get("access_level") or PUBLIC
        if row["access_level"] not in ACCESS_LEVELS:
            missing.append("access_level")
        if missing:
            rejected.append((i, missing))
            continue
        ms = _node(nodes, "manuscript", row["shelfmark"], row, "manuscript",
                   aliases=row.get("alt_titles", ""),
                   notes="; ".join(x for x in (row.get("title", ""), row.get("language", ""),
                                               row.get("script", ""), row.get("scan_uri", "")) if x))
        if row.get("title"):
            tx = _node(nodes, "text", row["title"], row, "work", aliases=row.get("alt_titles", ""))
            _edge(edges, ms, tx, "CONTAINS_TEXT", row)
        links = (("scribe", "person", "scribe", "COPIED_BY"), ("patron", "person", "patron", "COMMISSIONED_BY"),
                 ("place_of_production", "place", "production_place", "PRODUCED_AT"),
                 ("repository", "place", "repository", "HELD_AT"), ("material", "material", "material", "MADE_OF"))
        for col, ntype, cat, rel in links:
            if row.get(col):
                _edge(edges, ms, _node(nodes, ntype, row[col], row, cat), rel, row)
        if row.get("date_from") or row.get("date_to"):
            label = f"{row.get('date_from', '?')}-{row.get('date_to', '?')} CE"
            _edge(edges, ms, _node(nodes, "period", label, row, "date_range"), "DATED_TO", row)
    return nodes, edges, rejected


def read_catalogue(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, columns):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def write_graph(nodes, edges, out_dir):
    write_csv(f"{out_dir}/manuscript_nodes.csv", list(nodes.values()), NODE_COLUMNS)
    write_csv(f"{out_dir}/manuscript_edges.csv", edges, EDGE_COLUMNS)
