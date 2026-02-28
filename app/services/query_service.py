from app.ai.embeddings import embed_query
from app.storage.vector_store import search
from app.ai.llm import generate_answer


def answer_query(question):

    query_embedding = embed_query(question)

    chunks, metadata = search(query_embedding)

    context = "\n\n".join(chunks)

    answer = generate_answer(context, question)

    sources = []

    for i in range(len(chunks)):
        sources.append({
            "document": metadata[i]["document"],
            "text": chunks[i][:300]
        })

    return {
        "answer": answer,
        "sources": sources
    }