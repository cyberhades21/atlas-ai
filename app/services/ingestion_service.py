from app.utils.pdf_parser import extract_text
from app.ai.chunking import chunk_text
from app.ai.embeddings import embed_chunks
from app.storage.vector_store import store_embeddings


async def ingest_document(filepath, filename):

    print("Extracting text...")

    text = extract_text(filepath)

    print("Chunking...")

    chunks = chunk_text(text)

    print("Generating embeddings...")

    embeddings = embed_chunks(chunks)

    print("Storing vectors...")

    store_embeddings(chunks, embeddings, filename)

    print("Done indexing:", filename)