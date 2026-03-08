import ollama
import json


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


def call_llm_json(prompt):

    response = ollama.chat(
        model="mistral",
        messages=[
            {
                "role": "system",
                "content": "You are a system that extracts structured data and returns ONLY valid JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    content = response["message"]["content"]

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return []