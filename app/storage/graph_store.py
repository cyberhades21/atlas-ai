import sqlite3

conn = sqlite3.connect("data/graph.db", check_same_thread=False)

conn.execute("""
CREATE TABLE IF NOT EXISTS relationships (
    entity1 TEXT,
    relation TEXT,
    entity2 TEXT,
    document TEXT
)
""")


def store_relationships(triples, document):

    for t in triples:
        entity1 = t.get("entity1")
        relation = t.get("relation")
        entity2 = t.get("entity2")
        if not entity1 or not relation or not entity2:
            continue  
        conn.execute(
            "INSERT INTO relationships VALUES (?, ?, ?, ?)",
            (t["entity1"], t["relation"], t["entity2"], document)
        )

    conn.commit()


def search_relationships(keyword):

    cursor = conn.execute(
        """
        SELECT entity1, relation, entity2
        FROM relationships
        WHERE entity1 LIKE ? OR entity2 LIKE ?
        """,
        (f"%{keyword}%", f"%{keyword}%")
    )

    return cursor.fetchall()