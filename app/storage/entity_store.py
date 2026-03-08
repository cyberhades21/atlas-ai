import sqlite3

conn = sqlite3.connect("data/entities.db", check_same_thread=False)

conn.execute("""
CREATE TABLE IF NOT EXISTS entities (
    name TEXT,
    document TEXT
)
""")


def store_entities(entities, document):

    for entity in entities:
        conn.execute(
            "INSERT INTO entities VALUES (?, ?)",
            (entity, document)
        )

    conn.commit()


def search_entities(keyword):

    cursor = conn.execute(
        "SELECT name FROM entities WHERE name LIKE ?",
        (f"%{keyword}%",)
    )

    return [row[0] for row in cursor.fetchall()]