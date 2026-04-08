"""
File upload route.

POST /api/upload/resume — accept a PDF or TXT resume file,
                          extract its text, and return it for use in
                          the team member form before final submission.
"""

import io

from fastapi import APIRouter, HTTPException, UploadFile, status

router = APIRouter(prefix="/upload", tags=["upload"])

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "text/plain",
}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@router.post("/resume")
async def upload_resume(file: UploadFile) -> dict:
    """
    Extract plain text from an uploaded PDF or TXT resume.

    Returns:
        { "text": "<extracted resume text>", "filename": "<original filename>" }
    """
    content_type = (file.content_type or "").split(";")[0].strip()
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{content_type}'. Upload a PDF or plain-text file.",
        )

    raw = await file.read()

    if len(raw) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds the 5 MB limit.",
        )

    if content_type == "text/plain":
        try:
            text = raw.decode("utf-8", errors="replace")
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Could not decode text file: {exc}",
            ) from exc
    else:
        # PDF extraction via pypdf
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(raw))
            pages = [page.extract_text() or "" for page in reader.pages]
            text = "\n".join(pages).strip()
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Could not extract text from PDF: {exc}",
            ) from exc

    if not text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No text could be extracted from the file. Try a text-based PDF or paste your resume manually.",
        )

    return {"text": text, "filename": file.filename or "resume"}
