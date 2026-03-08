def chunk_text(text, size=2000, overlap=200):

    chunks = []

    start = 0

    while start < len(text):

        end = start + size

        chunk = text[start:end]

        chunks.append(chunk)

        start += size - overlap

    return chunks