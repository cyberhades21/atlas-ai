import sqlite3
from app.pipeline.graph_updates import graph_update_bus

conn = sqlite3.connect("data/graph.db", check_same_thread=False)

conn.execute("""
CREATE TABLE IF NOT EXISTS relationships (
    entity1 TEXT,
    relation TEXT,
    entity2 TEXT,
    document TEXT,
    UNIQUE(entity1, relation, entity2)
)
""")

# Migrate existing tables that lack the unique constraint by rebuilding them.
# This is a no-op on fresh databases.
_cols = {row[1] for row in conn.execute("PRAGMA table_info(relationships)")}
if "entity1" in _cols:
    conn.execute("""
    CREATE TABLE IF NOT EXISTS relationships_new (
        entity1 TEXT,
        relation TEXT,
        entity2 TEXT,
        document TEXT,
        UNIQUE(entity1, relation, entity2)
    )
    """)
    conn.execute("""
    INSERT OR IGNORE INTO relationships_new (entity1, relation, entity2, document)
    SELECT entity1, relation, entity2, document FROM relationships
    """)
    conn.execute("DROP TABLE relationships")
    conn.execute("ALTER TABLE relationships_new RENAME TO relationships")
    conn.commit()


def store_relationships(triples, document):
    saved = []
    for t in triples:
        entity1 = t.get("entity1")
        relation = t.get("relation")
        entity2 = t.get("entity2")
        if not entity1 or not relation or not entity2:
            continue
        cursor = conn.execute(
            "INSERT OR IGNORE INTO relationships VALUES (?, ?, ?, ?)",
            (entity1, relation, entity2, document)
        )
        if cursor.rowcount:  # 0 if the row already existed
            saved.append({"entity1": entity1, "relation": relation, "entity2": entity2})

    conn.commit()

    # Broadcast new triples to any connected graph viewers
    if saved:
        graph_update_bus.emit(saved)


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