from app.utils.pdf_parser import extract_text
from app.ai.chunking import chunk_text
from app.ai.embeddings import embed_chunks
from app.storage.vector_store import store_embeddings
from app.ai.relationship_extractor import extract_relationships
from app.storage.graph_store import store_relationships
from app.ai.entity_extractor import extract_entities
from app.storage.entity_store import store_entities


async def ingest_document(filepath, filename):

    print("Extracting text...")
    text = extract_text(filepath)

    print("Chunking...")
    chunks = chunk_text(text)

    all_relationships = []

    print("Extracting relationships...")
    all_entities = []
    all_relationships = []

    for chunk in chunks:
        entities = extract_entities(chunk)
        triples = extract_relationships(chunk)

        if entities:
            all_entities.extend(entities)

        if triples:
            all_relationships.extend(triples)

    print("Generating embeddings...")
    embeddings = embed_chunks(chunks)

    print("Storing vectors...")
    store_embeddings(chunks, embeddings, filename)
    
    print("Storing entities...")
    store_entities(all_entities, filename)


    print("Storing knowledge graph...")
    store_relationships(all_relationships, filename)

    print("Done indexing:", filename)