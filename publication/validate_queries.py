"""
validate_queries.py — Structural validation and recall checks for the Aksum KG.

Checks run (in order):
  1. CSV integrity  — column presence, no blank node_ids or edge_ids
  2. Referential integrity — every node_id in edges appears in nodes.csv
  3. Gold-set recall — all 51 gold nodes and 35 asserted edges present
  4. Duplication check — no duplicate node_ids; no duplicate (src, tgt, type) triples
  5. C14 completeness — all radiocarbon nodes have bp_age, cal_68pct, cal_95pct
  6. Source citation coverage — every node and edge has a non-blank source field
  7. (Optional Kuzu) — if a Kuzu DB path is provided, run openCypher queries
     and compare counts against CSV expectations.

Usage
-----
    python validate_queries.py                        # CSV-only checks
    python validate_queries.py --db_path aksum_kg.kuzu  # + Kuzu queries
    python validate_queries.py --data_dir publication/  # custom CSV dir
    python validate_queries.py --strict               # exit 1 on any failure

License: CC-BY-4.0 (derived graph data)
"""

import argparse
import csv
import pathlib
import sys
from collections import defaultdict
from typing import Any

# ---------------------------------------------------------------------------
# Expected gold counts (from methods_statement)
# ---------------------------------------------------------------------------
GOLD_NODE_COUNT = 51
GOLD_ASSERTED_EDGE_COUNT = 35
GOLD_HAND_CURATED_COUNT = 25
GOLD_AUTOMATED_COUNT = 10
GOLD_CANDIDATE_EDGE_COUNT = 15


# ---------------------------------------------------------------------------
# CSV field requirements
# ---------------------------------------------------------------------------
NODE_REQUIRED_COLS = [
    "node_id", "label", "crm_class", "entity_type",
    "source", "page_ref", "confidence",
]
AE_REQUIRED_COLS = [
    "edge_id", "source_node_id", "target_node_id",
    "relation_type", "relation_label", "evidence_type",
    "source", "page_ref", "extraction_method",
]
CE_REQUIRED_COLS = [
    "edge_id", "source_node_id", "target_node_id",
    "co_mention_count", "source", "page_ref",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class ValidationResult:
    def __init__(self) -> None:
        self.passed: list[str] = []
        self.warnings: list[str] = []
        self.failures: list[str] = []

    def ok(self, msg: str) -> None:
        self.passed.append(msg)
        print(f"  ✓  {msg}")

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)
        print(f"  ⚠  {msg}")

    def fail(self, msg: str) -> None:
        self.failures.append(msg)
        print(f"  ✗  {msg}")

    @property
    def success(self) -> bool:
        return len(self.failures) == 0


def _read_csv(path: pathlib.Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _check_columns(
    rows: list[dict], required: list[str], name: str, r: ValidationResult
) -> bool:
    if not rows:
        r.fail(f"{name}: file is empty")
        return False
    cols = set(rows[0].keys())
    missing = [c for c in required if c not in cols]
    if missing:
        r.fail(f"{name}: missing columns: {missing}")
        return False
    r.ok(f"{name}: all required columns present")
    return True


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------

def check_csv_integrity(
    nodes: list[dict],
    ae: list[dict],
    ce: list[dict],
    r: ValidationResult,
) -> None:
    print("\n[1] CSV integrity")

    _check_columns(nodes, NODE_REQUIRED_COLS, "nodes.csv", r)
    _check_columns(ae, AE_REQUIRED_COLS, "asserted_edges.csv", r)
    _check_columns(ce, CE_REQUIRED_COLS, "candidate_edges.csv", r)

    blank_nodes = [row["node_id"] for row in nodes if not row.get("node_id", "").strip()]
    if blank_nodes:
        r.fail(f"nodes.csv: {len(blank_nodes)} rows with blank node_id")
    else:
        r.ok("nodes.csv: no blank node_ids")

    for label, rows, col in [
        ("asserted_edges.csv", ae, "edge_id"),
        ("candidate_edges.csv", ce, "edge_id"),
    ]:
        blank = sum(1 for row in rows if not row.get(col, "").strip())
        if blank:
            r.fail(f"{label}: {blank} rows with blank {col}")
        else:
            r.ok(f"{label}: no blank {col}s")


def check_referential_integrity(
    nodes: list[dict],
    ae: list[dict],
    ce: list[dict],
    r: ValidationResult,
) -> None:
    print("\n[2] Referential integrity")
    known_ids = {row["node_id"] for row in nodes}

    for label, rows in [("asserted_edges.csv", ae), ("candidate_edges.csv", ce)]:
        missing_src = [
            row["edge_id"]
            for row in rows
            if row.get("source_node_id") not in known_ids
        ]
        missing_tgt = [
            row["edge_id"]
            for row in rows
            if row.get("target_node_id") not in known_ids
        ]
        if missing_src:
            r.fail(
                f"{label}: {len(missing_src)} edges reference unknown source node_ids"
                f" (first: {missing_src[0]})"
            )
        else:
            r.ok(f"{label}: all source node_ids resolve")
        if missing_tgt:
            r.fail(
                f"{label}: {len(missing_tgt)} edges reference unknown target node_ids"
                f" (first: {missing_tgt[0]})"
            )
        else:
            r.ok(f"{label}: all target node_ids resolve")


def check_gold_counts(
    nodes: list[dict],
    ae: list[dict],
    ce: list[dict],
    r: ValidationResult,
) -> None:
    print("\n[3] Gold-set counts")

    n = len(nodes)
    if n == GOLD_NODE_COUNT:
        r.ok(f"nodes.csv: {n} nodes (expected {GOLD_NODE_COUNT})")
    elif n > GOLD_NODE_COUNT:
        r.warn(
            f"nodes.csv: {n} nodes — {n - GOLD_NODE_COUNT} more than gold set "
            f"(expected {GOLD_NODE_COUNT}); this may reflect automated additions"
        )
    else:
        r.fail(f"nodes.csv: {n} nodes (expected {GOLD_NODE_COUNT})")

    ae_count = len(ae)
    if ae_count == GOLD_ASSERTED_EDGE_COUNT:
        r.ok(f"asserted_edges.csv: {ae_count} edges (expected {GOLD_ASSERTED_EDGE_COUNT})")
    else:
        r.fail(
            f"asserted_edges.csv: {ae_count} edges "
            f"(expected {GOLD_ASSERTED_EDGE_COUNT})"
        )

    hand = sum(1 for e in ae if e.get("extraction_method") == "hand_curated")
    auto = sum(1 for e in ae if e.get("extraction_method") == "regex_match")
    if hand == GOLD_HAND_CURATED_COUNT:
        r.ok(f"asserted_edges.csv: {hand} hand-curated edges (expected {GOLD_HAND_CURATED_COUNT})")
    else:
        r.fail(
            f"asserted_edges.csv: {hand} hand-curated edges "
            f"(expected {GOLD_HAND_CURATED_COUNT})"
        )
    if auto == GOLD_AUTOMATED_COUNT:
        r.ok(f"asserted_edges.csv: {auto} automated edges (expected {GOLD_AUTOMATED_COUNT})")
    else:
        r.fail(
            f"asserted_edges.csv: {auto} automated edges "
            f"(expected {GOLD_AUTOMATED_COUNT})"
        )

    ce_count = len(ce)
    if ce_count == GOLD_CANDIDATE_EDGE_COUNT:
        r.ok(f"candidate_edges.csv: {ce_count} candidate edges (expected {GOLD_CANDIDATE_EDGE_COUNT})")
    else:
        r.warn(
            f"candidate_edges.csv: {ce_count} candidate edges "
            f"(expected {GOLD_CANDIDATE_EDGE_COUNT})"
        )


def check_duplication(
    nodes: list[dict],
    ae: list[dict],
    r: ValidationResult,
) -> None:
    print("\n[4] Duplication")

    node_ids = [row["node_id"] for row in nodes]
    dup_nodes = {nid for nid in node_ids if node_ids.count(nid) > 1}
    if dup_nodes:
        r.fail(f"nodes.csv: duplicate node_ids: {dup_nodes}")
    else:
        r.ok("nodes.csv: no duplicate node_ids")

    ae_keys = [
        (e.get("source_node_id"), e.get("target_node_id"), e.get("relation_type"))
        for e in ae
    ]
    seen: set[tuple] = set()
    dups: list[tuple] = []
    for key in ae_keys:
        if key in seen:
            dups.append(key)
        seen.add(key)
    if dups:
        r.fail(
            f"asserted_edges.csv: {len(dups)} duplicate (src, tgt, relation_type) triples"
        )
    else:
        r.ok("asserted_edges.csv: no duplicate (src, tgt, relation_type) triples")


def check_c14_completeness(nodes: list[dict], r: ValidationResult) -> None:
    print("\n[5] Radiocarbon completeness")
    c14_nodes = [n for n in nodes if n.get("entity_type") == "radiocarbon"]
    incomplete = [
        n["node_id"]
        for n in c14_nodes
        if not n.get("bp_age", "").strip()
        or not n.get("cal_68pct", "").strip()
        or not n.get("cal_95pct", "").strip()
    ]
    if incomplete:
        r.fail(
            f"{len(incomplete)} radiocarbon node(s) missing bp_age/cal_68pct/cal_95pct: "
            f"{incomplete}"
        )
    else:
        r.ok(
            f"All {len(c14_nodes)} radiocarbon node(s) have bp_age, "
            "cal_68pct, and cal_95pct"
        )


def check_source_citation_coverage(
    nodes: list[dict],
    ae: list[dict],
    ce: list[dict],
    r: ValidationResult,
) -> None:
    print("\n[6] Source citation coverage")
    missing_node_src = [
        n["node_id"] for n in nodes if not n.get("source", "").strip()
    ]
    missing_ae_src = [
        e["edge_id"] for e in ae if not e.get("source", "").strip()
    ]
    missing_ce_src = [
        e["edge_id"] for e in ce if not e.get("source", "").strip()
    ]

    for label, missing in [
        ("nodes.csv", missing_node_src),
        ("asserted_edges.csv", missing_ae_src),
        ("candidate_edges.csv", missing_ce_src),
    ]:
        if missing:
            r.fail(f"{label}: {len(missing)} rows missing source field")
        else:
            r.ok(f"{label}: all rows have a source citation")

    # Check page_ref coverage too
    missing_node_pg = [
        n["node_id"] for n in nodes if not n.get("page_ref", "").strip()
    ]
    if missing_node_pg:
        r.warn(
            f"nodes.csv: {len(missing_node_pg)} nodes missing page_ref "
            f"(first: {missing_node_pg[0]})"
        )
    else:
        r.ok("nodes.csv: all rows have a page_ref")


# ---------------------------------------------------------------------------
# Optional Kuzu queries
# ---------------------------------------------------------------------------

def run_kuzu_checks(db_path: str, r: ValidationResult) -> None:
    print("\n[7] Kuzu graph checks")
    try:
        import kuzu
    except ImportError:
        r.warn("kuzu not installed — skipping graph checks")
        return

    db = kuzu.Database(db_path)
    conn = kuzu.Connection(db)

    queries: list[tuple[str, str, Any]] = [
        (
            "Total nodes",
            "MATCH (n:AksumEntity) RETURN count(n) AS c",
            GOLD_NODE_COUNT,
        ),
        (
            "Asserted edges",
            "MATCH ()-[r:ASSERTED_RELATION]->() RETURN count(r) AS c",
            GOLD_ASSERTED_EDGE_COUNT,
        ),
        (
            "Candidate edges",
            "MATCH ()-[r:CANDIDATE_RELATION]->() RETURN count(r) AS c",
            GOLD_CANDIDATE_EDGE_COUNT,
        ),
    ]

    for label, cypher, expected in queries:
        try:
            result = conn.execute(cypher)
            row = result.get_next()
            count = row[0] if row else None
            if count == expected:
                r.ok(f"Kuzu — {label}: {count} (expected {expected})")
            else:
                r.fail(
                    f"Kuzu — {label}: {count} (expected {expected})"
                )
        except Exception as exc:
            r.fail(f"Kuzu — {label}: query failed: {exc}")

    # Example analytical queries (printed but not validated against expected counts)
    print("\n  --- Example Kuzu queries ---")
    example_queries = [
        (
            "Gold-curated asserted edges only",
            "MATCH (a)-[r:ASSERTED_RELATION]->(b) "
            "WHERE r.extraction_method = 'hand_curated' "
            "RETURN a.label, r.relation_label, b.label LIMIT 5",
        ),
        (
            "All radiocarbon nodes with BP age",
            "MATCH (n:AksumEntity) WHERE n.entity_type = 'radiocarbon' "
            "RETURN n.label, n.bp_age, n.cal_68pct LIMIT 10",
        ),
        (
            "High co-mention candidate edges (count >= 3)",
            "MATCH (a)-[r:CANDIDATE_RELATION]->(b) "
            "WHERE r.co_mention_count >= 3 "
            "RETURN a.label, r.co_mention_count, b.label",
        ),
        (
            "Sites excavated by Phillipson",
            "MATCH (site)-[r:ASSERTED_RELATION]->(p:AksumEntity {node_id: 'person_phillipson_d'}) "
            "WHERE r.relation_label = 'excavated by' "
            "RETURN site.label, r.source, r.page_ref",
        ),
    ]
    for label, cypher in example_queries:
        print(f"\n  {label}:")
        print(f"    {cypher}")
        try:
            result = conn.execute(cypher)
            rows_seen = 0
            while result.has_next():
                row = result.get_next()
                print(f"      {row}")
                rows_seen += 1
            if rows_seen == 0:
                print("      (no results)")
        except Exception as exc:
            print(f"      ERROR: {exc}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Validate the Aksum KG CSVs and (optionally) a Kuzu graph."
    )
    parser.add_argument(
        "--data_dir",
        default="publication",
        help="Directory containing the CSV files (default: publication/)",
    )
    parser.add_argument(
        "--db_path",
        default=None,
        help="Path to an existing Kuzu database (optional)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 if any check fails",
    )
    args = parser.parse_args(argv)

    data_dir = pathlib.Path(args.data_dir)
    r = ValidationResult()

    print("=== Aksum KG Validation ===")
    print(f"Data directory: {data_dir.resolve()}\n")

    try:
        nodes = _read_csv(data_dir / "nodes.csv")
        ae = _read_csv(data_dir / "asserted_edges.csv")
        ce = _read_csv(data_dir / "candidate_edges.csv")
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    check_csv_integrity(nodes, ae, ce, r)
    check_referential_integrity(nodes, ae, ce, r)
    check_gold_counts(nodes, ae, ce, r)
    check_duplication(nodes, ae, r)
    check_c14_completeness(nodes, r)
    check_source_citation_coverage(nodes, ae, ce, r)

    if args.db_path:
        run_kuzu_checks(args.db_path, r)

    print("\n=== Summary ===")
    print(f"  Passed:   {len(r.passed)}")
    print(f"  Warnings: {len(r.warnings)}")
    print(f"  Failures: {len(r.failures)}")

    if r.failures:
        print("\nFailed checks:")
        for f in r.failures:
            print(f"  ✗ {f}")

    if args.strict and not r.success:
        sys.exit(1)

    if r.success:
        print("\nAll checks passed.")
    else:
        print(f"\n{len(r.failures)} check(s) failed.")


if __name__ == "__main__":
    main()
