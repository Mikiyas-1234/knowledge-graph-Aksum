"""Load manuscript_nodes.csv / manuscript_edges.csv into Neo4j over Bolt.

    python3 -m heritage_rag.load_neo4j <csv-dir> [--uri bolt://localhost:7687] [--user neo4j] [--password ...]

The password may also come from the NEO4J_PASSWORD environment variable.
"""
import argparse
import os

from . import ingest
from .store import Neo4jGraph


def read_graph(csv_dir):
    nodes = {r["id"]: r for r in ingest.read_catalogue(f"{csv_dir}/manuscript_nodes.csv")}
    edges = ingest.read_catalogue(f"{csv_dir}/manuscript_edges.csv")
    for row in (*nodes.values(), *edges):
        row["confidence"] = float(row["confidence"] or 1.0)
    return nodes, edges


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_dir")
    ap.add_argument("--uri", default="bolt://localhost:7687")
    ap.add_argument("--user", default="neo4j")
    ap.add_argument("--password", default=os.environ.get("NEO4J_PASSWORD"))
    args = ap.parse_args(argv)
    if not args.password:
        raise SystemExit("set --password or NEO4J_PASSWORD")
    nodes, edges = read_graph(args.csv_dir)
    graph = Neo4jGraph(args.uri, args.user, args.password)
    graph.load(nodes, edges)
    n, e = graph.count()
    print(f"loaded: {n} nodes, {e} relationships in Neo4j (expected {len(nodes)} nodes, {len(edges)} edges)")
    graph.close()


if __name__ == "__main__":
    main()
