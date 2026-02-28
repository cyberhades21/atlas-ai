from fastapi import APIRouter, UploadFile, File
import os

from app.services.ingestion_service import ingest_document

router = APIRouter(prefix="/documents")

UPLOAD_DIR = "data/documents"


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    filepath = os.path.join(UPLOAD_DIR, file.filename)

    with open(filepath, "wb") as f:
        f.write(await file.read())

    await ingest_document(filepath, file.filename)

    return {"status": "indexed"}