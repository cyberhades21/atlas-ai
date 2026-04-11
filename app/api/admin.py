from fastapi import APIRouter
from app.storage import vector_store, graph_store

router = APIRouter(prefix="/admin")


@router.delete("/flush")
def flush_all():
    """
    Wipe all vector embeddings and graph relationships.
    Intended for development / reset use only.
    """
    # --- Vector DB ---
    col = vector_store._get_collection()
    all_ids = col.get(include=[])["ids"]
    if all_ids:
        col.delete(ids=all_ids)

    # --- Graph DB ---
    graph_store.conn.execute("DELETE FROM relationships")
    graph_store.conn.commit()

    return {"status": "flushed", "vectors_removed": len(all_ids)}
