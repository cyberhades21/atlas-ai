from app.ai.embeddings import embed_query
from app.storage.vector_store import search
from app.ai.llm import generate_answer
from app.ai.entity_extractor import extract_entities
from app.storage.graph_store import search_relationships


def answer_query(question):

    # Step 1: extract entities from the question
    entities = extract_entities(question)

    # Step 2: search knowledge graph
    graph_context = ""

    for entity in entities:

        relations = search_relationships(entity)

        for a, r, b in relations:
            graph_context += f"{a} {r} {b}\n"

    # Step 3: vector search
    query_embedding = embed_query(question)

    chunks, metadata = search(query_embedding)

    vector_context = "\n\n".join(chunks)

    # Step 4: combine contexts
    context = graph_context + "\n\n" + vector_context

    # Step 5: generate answer
    answer = generate_answer(context, question)

    sources = []

    for i in range(len(chunks)):
        sources.append({
            "document": metadata[i]["document"],
            "text": chunks[i][:300]
        })

    return {
        "answer": answer,
        "entities": entities,
        "graph_context": graph_context,
        "sources": sources
    }