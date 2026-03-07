from fastapi import APIRouter
import chromadb
from sklearn.decomposition import PCA

router = APIRouter()

client = chromadb.PersistentClient(path="data/vector_db")


@router.get("/vectors")
def inspect_vectors():

    collection = client.get_collection("atlas")

    data = collection.get(include=["embeddings", "documents", "metadatas"])

    embeddings = data["embeddings"]
    documents = data["documents"]
    metadatas = data["metadatas"]

    pca = PCA(n_components=2)
    reduced = pca.fit_transform(embeddings)

    vectors = []

    for i in range(len(reduced)):
        vectors.append({
            "x": float(reduced[i][0]),
            "y": float(reduced[i][1]),
            "text": documents[i][:120],
            "document": metadatas[i]["document"]
        })

    return vectors