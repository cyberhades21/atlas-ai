from fastapi import APIRouter
from app.storage.graph_store import conn

router = APIRouter()


@router.get("/graph")
def get_graph():

    cursor = conn.execute(
        "SELECT entity1, relation, entity2 FROM relationships"
    )

    nodes = set()
    edges = []

    rows = cursor.fetchall()

    for entity1, relation, entity2 in rows:

        nodes.add(entity1)
        nodes.add(entity2)

        edges.append({
            "data": {
                "source": entity1,
                "target": entity2,
                "label": relation
            }
        })

    node_list = []

    for n in nodes:
        node_list.append({
            "data": {
                "id": n
            }
        })

    return {
        "nodes": node_list,
        "edges": edges
    }