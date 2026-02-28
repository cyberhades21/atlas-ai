# Atlas AI – Local Setup Guide


Atlas AI is a local AI knowledge assistant that indexes documents and answers questions using a Retrieval-Augmented Generation (RAG) pipeline.

---

## 1. Prerequisites

Install the following before continuing.

### Python 3.11

Verify installation:

```
python --version
```

Expected output:

```
Python 3.11.x
```

---

### Ollama

Install Ollama:

https://ollama.com

Verify installation:

```
ollama --version
```

---

## 2. Install Required Models

Pull the required models:

```
ollama pull mistral
```

```
ollama pull nomic-embed-text
```

Verify:

```
ollama list
```

Expected:

```
mistral
nomic-embed-text
```

---

## 3. Clone Repository

```
git clone <repository-url>
```

```
cd atlas-ai
```

---

## 4. Create Virtual Environment

```
py -3.11 -m venv venv
```

Activate environment:

```
venv\Scripts\activate
```

---

## 5. Install Dependencies

```
pip install -r requirements.txt
```

---

## 6. Create Required Folders

Create the required folders if they do not exist:

```
mkdir data
mkdir data\documents
mkdir data\vector_db
```

Required structure:

```
data/
 ├ documents/
 └ vector_db/
```

---

## 7. Start Atlas AI

Activate environment:

```
venv\Scripts\activate
```

Start server:

```
uvicorn app.main:app --reload
```

Open Swagger UI:

```
http://localhost:8000/docs
```

---

## 8. Upload Documents

Endpoint:

```
POST /documents/upload
```

Upload a PDF document.

Documents are automatically indexed after upload.

---

## 9. Ask Questions

Endpoint:

```
POST /query
```

Example request body:

```
{
  "question": "What is the cancellation policy?"
}
```

---

## 10. Stop Server

Stop the FastAPI server:

```
CTRL + C
```

---

## 11. Unload AI Models (Free Memory)

List running models:

```
ollama ps
```

Stop models:

```
ollama stop mistral
```

```
ollama stop nomic-embed-text
```

Verify unloaded:

```
ollama ps
```

Expected:

```
No running models
```

---

## 12. Reset Indexed Data

Delete vector database:

```
rmdir /s data\vector_db
```

Recreate:

```
mkdir data\vector_db
```

---

## 13. Reset Uploaded Documents

Delete documents:

```
rmdir /s data\documents
```

Recreate:

```
mkdir data\documents
```

---

## 14. Full Reset

Stop server and remove all stored data:

```
CTRL + C
```

```
rmdir /s data
```

Recreate folders:

```
mkdir data
mkdir data\documents
mkdir data\vector_db
```

Start server:

```
uvicorn app.main:app --reload
```

Atlas AI will start with a clean state.

---

## 15. Verify GPU Usage (Optional)

During queries you should see GPU usage increase:

```
nvidia-smi
```

---

## 17. Default URLs

API:

```
http://localhost:8000
```

Swagger UI:

```
http://localhost:8000/docs
```

---