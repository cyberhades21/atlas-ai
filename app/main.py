from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.documents import router as document_router
from app.api.query import router as query_router
from app.api.debug import router as debug_router

app = FastAPI(title="Atlas AI")

app.include_router(document_router)
app.include_router(query_router)
app.include_router(debug_router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
def home():
    return FileResponse("app/static/index.html")

@app.get("/vectors-ui")
def vectors_page():
    return FileResponse("app/static/vectors.html")