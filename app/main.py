from fastapi import FastAPI
from app.api.documents import router as document_router
from app.api.query import router as query_router

app = FastAPI(title="Atlas AI")

app.include_router(document_router)
app.include_router(query_router)


@app.get("/")
def root():
    return {"message": "Atlas AI Running"}