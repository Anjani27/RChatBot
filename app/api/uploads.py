"""Uploads API — PDF file upload and RAG indexing with user isolation."""
import os
import uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status

from app.core.config import UPLOAD_DIR
from app.services.rag_service import index_uploaded_pdf
from app.services import conversation_service as svc
from app.services.auth_service import get_current_user
from app.repositories import conversation_repository as repo

router = APIRouter(prefix="/api/upload", tags=["uploads"])


@router.post("")
async def upload_pdf(
    file: UploadFile = File(...),
    thread_id: str = Form(...),
    current_user: str = Depends(get_current_user)
):
    """
    Accept a PDF upload, save it locally, and index it into Chroma DB
    under the given thread_id so RAG queries in that conversation use it.
    Only allows upload if the conversation belongs to the user.
    """
    # Verify ownership
    owner = repo.get_owner(thread_id)
    if owner and owner != current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this conversation."
        )

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    # Make sure the conversation exists and belongs to the user
    svc.ensure_conversation(thread_id, email=current_user)

    # Save the file
    thread_upload_dir = os.path.join(UPLOAD_DIR, thread_id)
    os.makedirs(thread_upload_dir, exist_ok=True)

    safe_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(thread_upload_dir, safe_filename)

    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    # Index into Chroma
    try:
        chunks_indexed = index_uploaded_pdf(file_path, thread_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {e}")

    return {
        "status": "success",
        "filename": file.filename,
        "thread_id": thread_id,
        "chunks_indexed": chunks_indexed,
    }
