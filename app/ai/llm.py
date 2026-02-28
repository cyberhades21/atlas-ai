import ollama


def generate_answer(context, question):

    prompt = f"""
Answer using ONLY the context below.

If the answer is not found, say "Not found in documents".

Context:
{context}

Question:
{question}
"""

    response = ollama.chat(
        model="mistral",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response["message"]["content"]