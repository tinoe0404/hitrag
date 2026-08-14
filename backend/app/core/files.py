import os
import uuid
from typing import Tuple
from fastapi import UploadFile, HTTPException, status

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB max file size limit
CHUNK_SIZE_BYTES = 1024 * 1024  # 1 MB stream buffer chunk

def save_upload(file: UploadFile) -> Tuple[str, str]:
    """
    Validates, streams, and saves an uploaded PDF document file to disk under uploads/.
    
    Checks:
    1. Extension is .pdf (case insensitive).
    2. Content-Type header is application/pdf.
    3. Magic bytes (%PDF-) at the start of the streamed file content.
    4. Enforces max file size (20MB) during streaming without loading entire file to memory.
    5. Generates collision-safe disk filename (uuid4 + .pdf).
    """
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()

    if ext != ".pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only PDF documents (.pdf) are allowed."
        )

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Content-Type. Expected 'application/pdf'."
        )

    # Ensure uploads target directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    generated_filename = f"{uuid.uuid4().hex}.pdf"
    storage_path = os.path.join(UPLOAD_DIR, generated_filename)

    total_bytes = 0
    header_checked = False

    try:
        with open(storage_path, "wb") as buffer:
            while chunk := file.file.read(CHUNK_SIZE_BYTES):
                if not header_checked:
                    # Validate PDF Magic Bytes (%PDF-)
                    if not chunk.startswith(b"%PDF-"):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid PDF content. Magic byte signature check failed."
                        )
                    header_checked = True

                total_bytes += len(chunk)
                if total_bytes > MAX_FILE_SIZE_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                        detail=f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB."
                    )
                buffer.write(chunk)
    except Exception as e:
        # Cleanup partially written file on disk if streaming failed
        if os.path.exists(storage_path):
            os.remove(storage_path)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save upload file: {str(e)}"
        )

    return generated_filename, storage_path

def delete_upload_file(storage_path: str) -> None:
    """Safely delete file on disk if present."""
    if storage_path and os.path.exists(storage_path):
        try:
            os.remove(storage_path)
        except OSError:
            pass
