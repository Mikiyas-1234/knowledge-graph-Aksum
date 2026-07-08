"""
Load the publication graph into an embedded Kuzu database and run validation
queries. Kuzu speaks openCypher (the same query language Neo4j uses) but,
unlike Neo4j, requires node/relationship TABLES declared up front -- this is
a Kuzu constraint, not a difference in the data model itself. The
`aksum_kg_publication.cypher` file remains the correct artifact for real
Neo4j (Desktop/Docker/Aura), where CREATE works schema-free.
"""
import kuzu, csv, shutil, os

DB_PATH = "/home/claude/aksum_kg/publication/kuzu_db"
if os.path.exists(DB_PATH):
    shutil.rmtree(DB_PATH)

db = kuzu.Database(DB_PATH)
conn = kuzu.Connection(db)

conn.execute("""
CREATE NODE TABLE Entity(
  id STRING PRIMARY KEY, label STRING, cidoc_class STRING, category STRING,
  source_document STRING, source_locator STRING, epistemic_provenance STRING,
  confidence DOUBLE, notes STRING
)
""")

ASSERTED_TYPES = ['ASSOCIATED_WITH','BEARS_NAME_OF','CREATED_BY_COMMISSION_OF','DATED_TO',
    'DATES_CONTEXT_AT','DISTURBED_DURING','EXCAVATED_BY','FOUND_AT','LOCATED_AT','MADE_OF',
    'PART_OF','PREDECESSOR_COMMUNITY_OF','RULED_BY']

for rt in ASSERTED_TYPES:
    conn.execute(f"""
    CREATE REL TABLE {rt}(
      FROM Entity TO Entity, status STRING, cidoc_property STRING,
      source_document STRING, source_locator STRING, evidence_type STRING,
      confidence DOUBLE, notes STRING
    )""")

conn.execute("""
CREATE REL TABLE CO_OCCURS_WITH(
  FROM Entity TO Entity, status STRING, co_mention_count INT64,
  source_document STRING, source_locator STRING, notes STRING
)""")

# ---- Load nodes ----
nodes_path = os.path.abspath("nodes.csv")
conn.execute(f"COPY Entity FROM '{nodes_path}' (header=true)")

# ---- Split asserted edges by relationship type and load each ----
by_type = {rt: [] for rt in ASSERTED_TYPES}
with open("asserted_edges.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        by_type[row["relationship"]].append(row)

for rt, rows in by_type.items():
    if not rows:
        continue
    path = f"/tmp/rel_{rt}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["source","target","status","cidoc_property","source_document","source_locator","evidence_type","confidence","notes"])
        for r in rows:
            w.writerow([r["source"], r["target"], "asserted", r["cidoc_property"],
                        r["source_document"], r["source_locator"], r["evidence_type"],
                        r["confidence"], r["notes"]])
    conn.execute(f"COPY {rt} FROM '{path}' (header=true)")

# ---- Candidate edges ----
path = "/tmp/rel_CO_OCCURS_WITH.csv"
with open("candidate_edges.csv", encoding="utf-8") as f_in, open(path, "w", newline="", encoding="utf-8") as f_out:
    w = csv.writer(f_out)
    w.writerow(["source","target","status","co_mention_count","source_document","source_locator","notes"])
    for r in csv.DictReader(f_in):
        w.writerow([r["source"], r["target"], "candidate", r["co_mention_count"],
                    r["source_document"], r["source_locator"], r["notes"]])
conn.execute(f"COPY CO_OCCURS_WITH FROM '{path}' (header=true)")

print("=== LOAD COMPLETE ===")
r = conn.execute("MATCH (n:Entity) RETURN count(n) AS n").get_next()
print("Total nodes loaded:", r[0])
