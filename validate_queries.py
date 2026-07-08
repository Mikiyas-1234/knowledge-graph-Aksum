import kuzu

db = kuzu.Database("/home/claude/aksum_kg/publication/kuzu_db")
conn = kuzu.Connection(db)

def run(title, query):
    print(f"\n--- {title} ---")
    result = conn.execute(query)
    cols = result.get_column_names()
    print(" | ".join(cols))
    n = 0
    while result.has_next():
        row = result.get_next()
        print(" | ".join(str(x) for x in row))
        n += 1
        if n >= 15:
            print("... (truncated)")
            break

run("Node counts by CIDOC class",
    "MATCH (n:Entity) RETURN n.cidoc_class AS class, count(*) AS n ORDER BY n DESC")

run("Edge counts by relationship type (asserted only)", """
MATCH (a:Entity)-[r:FOUND_AT]->(b:Entity) RETURN 'FOUND_AT' AS rel, count(*) AS n
UNION ALL
MATCH (a:Entity)-[r:EXCAVATED_BY]->(b:Entity) RETURN 'EXCAVATED_BY' AS rel, count(*) AS n
UNION ALL
MATCH (a:Entity)-[r:DATED_TO]->(b:Entity) RETURN 'DATED_TO' AS rel, count(*) AS n
UNION ALL
MATCH (a:Entity)-[r:DATES_CONTEXT_AT]->(b:Entity) RETURN 'DATES_CONTEXT_AT' AS rel, count(*) AS n
UNION ALL
MATCH (a:Entity)-[r:RULED_BY]->(b:Entity) RETURN 'RULED_BY' AS rel, count(*) AS n
""")

run("Everything asserted-connected to Aksum (place_aksum)", """
MATCH (a:Entity {id:'place_aksum'})-[r:FOUND_AT|EXCAVATED_BY|RULED_BY|PART_OF|LOCATED_AT]-(b:Entity)
RETURN b.label AS connected_entity, b.cidoc_class AS class
""")

run("Radiocarbon measurements and what they date", """
MATCH (m:Entity)-[r:DATES_CONTEXT_AT]->(ctx:Entity)
RETURN m.label AS measurement, ctx.label AS dated_context, m.notes AS detail
""")

run("Top 10 candidate co-occurrence pairs by frequency (review queue)", """
MATCH (a:Entity)-[r:CO_OCCURS_WITH]->(b:Entity)
RETURN a.label AS entity_a, b.label AS entity_b, r.co_mention_count AS co_mentions
ORDER BY r.co_mention_count DESC LIMIT 10
""")

run("Confirm single Aksum node (no Axum duplicate)",
    "MATCH (n:Entity) WHERE n.label CONTAINS 'ksum' AND n.cidoc_class = 'E53_Place' RETURN n.id, n.label")

run("2-hop path: King Ezana -> ruled -> Aksum -> located features/objects", """
MATCH (p:Entity {id:'person_ezana'})<-[:RULED_BY]-(place:Entity)-[:FOUND_AT|LOCATED_AT]-(thing:Entity)
RETURN place.label AS place, thing.label AS related_thing, thing.cidoc_class AS class
""")
