"""
load_kuzu.py — Load the Aksum Knowledge Graph CSVs into an embedded Kuzu database.

Kuzu is an openCypher-compatible embedded graph database — no server required.
This script creates the schema, loads nodes.csv, asserted_edges.csv, and
candidate_edges.csv, then prints a brief summary.

Usage
-----
    pip install kuzu
    python load_kuzu.py                          # creates ./aksum_kg.kuzu/
    python load_kuzu.py --db_path /tmp/my_kg     # custom path
    python load_kuzu.py --data_dir publication/  # custom CSV directory
    python load_kuzu.py --drop_existing          # wipe and recreate

After loading, run validate_queries.py or open kuzu-explorer for interactive
queries.

License: CC-BY-4.0 (derived graph data)
"""

import argparse
import csv
import pathlib
import sys

try:
    import kuzu
except ImportError:
    print(
        "kuzu is not installed.  Run:  pip install kuzu",
        file=sys.stderr,
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

NODE_TABLE_DDL = """
CREATE NODE TABLE IF NOT EXISTS AksumEntity (
    node_id     STRING,
    label       STRING,
    crm_class   STRING,
    entity_type STRING,
    source      STRING,
    page_ref    STRING,
    confidence  STRING,
    bp_age      STRING,
    cal_68pct   STRING,
    cal_95pct   STRING,
    lab_material STRING,
    notes       STRING,
    PRIMARY KEY (node_id)
)
"""

# Asserted relationships — typed by CRM property for easy filtering
ASSERTED_EDGE_DDL = """
CREATE REL TABLE IF NOT EXISTS ASSERTED_RELATION (
    FROM AksumEntity TO AksumEntity,
    edge_id           STRING,
    relation_type     STRING,
    relation_label    STRING,
    evidence_type     STRING,
    source            STRING,
    page_ref          STRING,
    extraction_method STRING,
    notes             STRING,
    status            STRING
)
"""

CANDIDATE_EDGE_DDL = """
CREATE REL TABLE IF NOT EXISTS CANDIDATE_RELATION (
    FROM AksumEntity TO AksumEntity,
    edge_id           STRING,
    co_mention_count  INT64,
    source            STRING,
    page_ref          STRING,
    sentence_context  STRING,
    notes             STRING,
    status            STRING
)
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_csv(path: pathlib.Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _safe_int(val: str, default: int = 0) -> int:
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_nodes(conn: "kuzu.Connection", rows: list[dict]) -> int:
    loaded = 0
    for row in rows:
        conn.execute(
            """
            MERGE (n:AksumEntity {node_id: $node_id})
            SET n.label        = $label,
                n.crm_class    = $crm_class,
                n.entity_type  = $entity_type,
                n.source       = $source,
                n.page_ref     = $page_ref,
                n.confidence   = $confidence,
                n.bp_age       = $bp_age,
                n.cal_68pct    = $cal_68pct,
                n.cal_95pct    = $cal_95pct,
                n.lab_material = $lab_material,
                n.notes        = $notes
            """,
            parameters={
                "node_id":      row.get("node_id", ""),
                "label":        row.get("label", ""),
                "crm_class":    row.get("crm_class", ""),
                "entity_type":  row.get("entity_type", ""),
                "source":       row.get("source", ""),
                "page_ref":     row.get("page_ref", ""),
                "confidence":   row.get("confidence", ""),
                "bp_age":       row.get("bp_age", ""),
                "cal_68pct":    row.get("cal_68pct", ""),
                "cal_95pct":    row.get("cal_95pct", ""),
                "lab_material": row.get("lab_material", ""),
                "notes":        row.get("notes", ""),
            },
        )
        loaded += 1
    return loaded


def load_asserted_edges(conn: "kuzu.Connection", rows: list[dict]) -> tuple[int, int]:
    loaded = 0
    skipped = 0
    for row in rows:
        src = row.get("source_node_id", "")
        tgt = row.get("target_node_id", "")
        if not src or not tgt:
            skipped += 1
            continue
        conn.execute(
            """
            MATCH (a:AksumEntity {node_id: $src}),
                  (b:AksumEntity {node_id: $tgt})
            CREATE (a)-[:ASSERTED_RELATION {
                edge_id:           $edge_id,
                relation_type:     $relation_type,
                relation_label:    $relation_label,
                evidence_type:     $evidence_type,
                source:            $source,
                page_ref:          $page_ref,
                extraction_method: $extraction_method,
                notes:             $notes,
                status:            'asserted'
            }]->(b)
            """,
            parameters={
                "src":               src,
                "tgt":               tgt,
                "edge_id":           row.get("edge_id", ""),
                "relation_type":     row.get("relation_type", ""),
                "relation_label":    row.get("relation_label", ""),
                "evidence_type":     row.get("evidence_type", ""),
                "source":            row.get("source", ""),
                "page_ref":          row.get("page_ref", ""),
                "extraction_method": row.get("extraction_method", ""),
                "notes":             row.get("notes", ""),
            },
        )
        loaded += 1
    return loaded, skipped


def load_candidate_edges(conn: "kuzu.Connection", rows: list[dict]) -> tuple[int, int]:
    loaded = 0
    skipped = 0
    for row in rows:
        src = row.get("source_node_id", "")
        tgt = row.get("target_node_id", "")
        if not src or not tgt:
            skipped += 1
            continue
        conn.execute(
            """
            MATCH (a:AksumEntity {node_id: $src}),
                  (b:AksumEntity {node_id: $tgt})
            CREATE (a)-[:CANDIDATE_RELATION {
                edge_id:          $edge_id,
                co_mention_count: $co_mention_count,
                source:           $source,
                page_ref:         $page_ref,
                sentence_context: $sentence_context,
                notes:            $notes,
                status:           'candidate'
            }]->(b)
            """,
            parameters={
                "src":              src,
                "tgt":              tgt,
                "edge_id":          row.get("edge_id", ""),
                "co_mention_count": _safe_int(row.get("co_mention_count", "0")),
                "source":           row.get("source", ""),
                "page_ref":         row.get("page_ref", ""),
                "sentence_context": row.get("sentence_context", ""),
                "notes":            row.get("notes", ""),
            },
        )
        loaded += 1
    return loaded, skipped


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Load the Aksum KG CSVs into an embedded Kuzu database."
    )
    parser.add_argument(
        "--db_path",
        default="aksum_kg.kuzu",
        help="Path to the Kuzu database directory (default: ./aksum_kg.kuzu)",
    )
    parser.add_argument(
        "--data_dir",
        default="publication",
        help="Directory containing nodes.csv, asserted_edges.csv, candidate_edges.csv",
    )
    parser.add_argument(
        "--drop_existing",
        action="store_true",
        help="Drop and recreate all tables before loading",
    )
    args = parser.parse_args(argv)

    data_dir = pathlib.Path(args.data_dir)
    nodes_path = data_dir / "nodes.csv"
    asserted_path = data_dir / "asserted_edges.csv"
    candidate_path = data_dir / "candidate_edges.csv"

    for p in (nodes_path, asserted_path, candidate_path):
        if not p.exists():
            print(f"Error: required file not found: {p}", file=sys.stderr)
            sys.exit(1)

    print(f"Opening Kuzu database at: {args.db_path}")
    db = kuzu.Database(args.db_path)
    conn = kuzu.Connection(db)

    if args.drop_existing:
        print("Dropping existing tables…")
        for tbl in ("CANDIDATE_RELATION", "ASSERTED_RELATION", "AksumEntity"):
            try:
                conn.execute(f"DROP TABLE {tbl}")
                print(f"  Dropped {tbl}")
            except Exception:
                pass

    print("Creating schema…")
    conn.execute(NODE_TABLE_DDL)
    conn.execute(ASSERTED_EDGE_DDL)
    conn.execute(CANDIDATE_EDGE_DDL)

    print(f"Loading nodes from {nodes_path}…")
    node_rows = _read_csv(nodes_path)
    n_nodes = load_nodes(conn, node_rows)
    print(f"  Loaded {n_nodes} nodes")

    print(f"Loading asserted edges from {asserted_path}…")
    ae_rows = _read_csv(asserted_path)
    n_ae, skip_ae = load_asserted_edges(conn, ae_rows)
    print(f"  Loaded {n_ae} asserted edges ({skip_ae} skipped — missing node IDs)")

    print(f"Loading candidate edges from {candidate_path}…")
    ce_rows = _read_csv(candidate_path)
    n_ce, skip_ce = load_candidate_edges(conn, ce_rows)
    print(f"  Loaded {n_ce} candidate edges ({skip_ce} skipped — missing node IDs)")

    print("\nSummary")
    print(f"  Nodes:           {n_nodes}")
    print(f"  Asserted edges:  {n_ae}")
    print(f"  Candidate edges: {n_ce}")
    print(f"\nDatabase ready at: {args.db_path}")
    print("Run  python validate_queries.py  to verify the graph.")


if __name__ == "__main__":
    main()
