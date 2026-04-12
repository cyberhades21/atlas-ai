import sqlite3
from app.pipeline.graph_updates import graph_update_bus
from app.ai.entity_normalizer import normalize_entity, normalize_relation

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

# Indexes speed up the IN-clause queries used by N-hop traversal.
conn.execute("CREATE INDEX IF NOT EXISTS idx_rel_entity1 ON relationships(entity1)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_rel_entity2 ON relationships(entity2)")

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
        entity1 = normalize_entity(t.get("entity1") or "")
        relation = normalize_relation(t.get("relation") or "")
        entity2 = normalize_entity(t.get("entity2") or "")
        # Guard AFTER normalization — a name that strips to "" is discarded
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


# Hard cap on triples returned by nhop — prevents flooding the LLM context.
MAX_GRAPH_RESULTS = 500
# SQLite's parameter limit is 999; the frontier list appears twice in the
# IN-clause query, so we chunk at 499.
_SQLITE_MAX_PARAMS = 499


def search_relationships_nhop(keywords: list, hops: int = 2) -> list:
    """
    Multi-hop BFS graph traversal starting from seed nodes matched by keyword.

    keywords : raw query strings — normalized internally before lookup
    hops     : number of edge hops to follow from each seed (default 2)
    returns  : deduplicated list of (entity1, relation, entity2) tuples,
               capped at MAX_GRAPH_RESULTS

    Hop 0 (seed discovery) uses LIKE matching on normalized keywords so it
    still finds un-normalized legacy data in existing graphs.
    Hops 1+ use exact IN-clause queries covered by the entity indexes.
    """
    normalized = [normalize_entity(k) for k in keywords if k]
    normalized = [k for k in normalized if k]
    if not normalized:
        return []

    # --- Seed discovery: LIKE match per keyword ---
    seed_nodes: set[str] = set()
    for kw in normalized:
        cursor = conn.execute(
            "SELECT DISTINCT entity1 FROM relationships WHERE entity1 LIKE ? "
            "UNION "
            "SELECT DISTINCT entity2 FROM relationships WHERE entity2 LIKE ?",
            (f"%{kw}%", f"%{kw}%"),
        )
        for row in cursor.fetchall():
            seed_nodes.add(row[0])

    if not seed_nodes:
        return []

    # --- BFS expansion ---
    visited: set[str] = set(seed_nodes)
    frontier: set[str] = set(seed_nodes)
    collected: set[tuple] = set()

    for _ in range(hops):
        if not frontier:
            break
        next_frontier: set[str] = set()

        # Chunk the frontier to stay within SQLite's parameter limit
        frontier_list = list(frontier)
        for i in range(0, len(frontier_list), _SQLITE_MAX_PARAMS):
            chunk = frontier_list[i: i + _SQLITE_MAX_PARAMS]
            ph = ",".join("?" * len(chunk))
            rows = conn.execute(
                f"SELECT entity1, relation, entity2 FROM relationships "
                f"WHERE entity1 IN ({ph}) OR entity2 IN ({ph})",
                chunk + chunk,
            ).fetchall()
            for e1, rel, e2 in rows:
                collected.add((e1, rel, e2))
                if e1 not in visited:
                    next_frontier.add(e1)
                    visited.add(e1)
                if e2 not in visited:
                    next_frontier.add(e2)
                    visited.add(e2)

        frontier = next_frontier

    return list(collected)[:MAX_GRAPH_RESULTS]