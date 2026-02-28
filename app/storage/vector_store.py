import chromadb

client = chromadb.PersistentClient(path="data/vector_db")

collection = client.get_or_create_collection("atlas")


def store_embeddings(chunks, embeddings, filename):

    ids = []
    metadatas = []

    for i in range(len(chunks)):

        ids.append(f"{filename}_{i}")

        metadatas.append({
            "document": filename
        })

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas
    )


def search(query_embedding):

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=5
    )

    return (
        results["documents"][0],
        results["metadatas"][0]
    )