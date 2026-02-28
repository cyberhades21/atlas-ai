import ollama


def embed_chunks(chunks):

    embeddings = []

    for chunk in chunks:

        response = ollama.embeddings(
            model="nomic-embed-text",
            prompt=chunk
        )

        embeddings.append(response["embedding"])

    return embeddings


def embed_query(text):

    response = ollama.embeddings(
        model="nomic-embed-text",
        prompt=text
    )

    return response["embedding"]