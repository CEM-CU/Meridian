"""Upload routes for job descriptions and CVs.

Accepts either multipart file uploads (PDF or plain text) or
JSON bodies with a ``text`` field and returns extracted text
with metadata.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from starlette.datastructures import UploadFile

from meridian.common.pdf import extract_text_from_pdf

logger = logging.getLogger(__name__)

router = APIRouter()

_PDF_CONTENT_TYPES = {"application/pdf"}
_MAX_TEXT_BYTES = 5 * 1024 * 1024  # 5 MB guard


class TextBody(BaseModel):
    """JSON body for raw-text uploads."""

    text: str


class UploadResponse(BaseModel):
    """Structured response from an upload endpoint."""

    text: str
    char_count: int
    source: str  # "pdf" | "text" | "paste"


def _make_response(text: str, source: str) -> UploadResponse:
    """Build an UploadResponse, rejecting empty text."""
    stripped = text.strip()
    if not stripped:
        raise HTTPException(status_code=400, detail="Uploaded content contains no extractable text.")
    return UploadResponse(text=stripped, char_count=len(stripped), source=source)


async def _handle_request(request: Request) -> UploadResponse:
    """Dispatch to the correct extraction path based on Content-Type."""
    content_type = (request.headers.get("content-type") or "").split(";")[0].strip().lower()

    # --- JSON / paste path ---
    if content_type == "application/json":
        try:
            payload = await request.json()
            body = TextBody.model_validate(payload)
        except (ValidationError, Exception) as exc:
            raise HTTPException(status_code=422, detail=f"Invalid JSON body: {exc}") from exc
        return _make_response(body.text, "paste")

    # --- Multipart file upload ---
    if "multipart/form-data" in content_type:
        form = await request.form()
        file = form.get("file")
        if file is None or not isinstance(file, UploadFile):
            raise HTTPException(status_code=422, detail="Multipart form must include a 'file' field.")

        raw: bytes = await file.read()
        if len(raw) > _MAX_TEXT_BYTES:
            raise HTTPException(status_code=413, detail="File exceeds the 5 MB limit.")

        file_content_type = (file.content_type or "").split(";")[0].strip().lower()
        filename_lower = (file.filename or "").lower()

        if file_content_type in _PDF_CONTENT_TYPES or filename_lower.endswith(".pdf"):
            try:
                text = extract_text_from_pdf(raw)
            except ValueError as exc:
                raise HTTPException(status_code=422, detail=f"PDF extraction failed: {exc}") from exc
            return _make_response(text, "pdf")

        # Plain-text fallback: attempt UTF-8 then latin-1
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("latin-1")
        return _make_response(text, "text")

    raise HTTPException(
        status_code=415,
        detail="Unsupported media type. Use 'application/json' or 'multipart/form-data'.",
    )


# ---------------------------------------------------------------------------
# /api/upload/jd
# ---------------------------------------------------------------------------


@router.post("/jd", response_model=UploadResponse)
async def upload_jd(request: Request) -> JSONResponse:
    """Accept a job-description document and return extracted text.

    Accepts either a multipart ``file`` (PDF or plain text) or a JSON
    ``body`` with a ``text`` field.  Returns ``{"text", "char_count", "source"}``.
    """
    result = await _handle_request(request)
    return JSONResponse(content=result.model_dump())


# ---------------------------------------------------------------------------
# /api/upload/cv
# ---------------------------------------------------------------------------


@router.post("/cv", response_model=UploadResponse)
async def upload_cv(request: Request) -> JSONResponse:
    """Accept a CV document and return extracted text.

    Accepts either a multipart ``file`` (PDF or plain text) or a JSON
    ``body`` with a ``text`` field.  Returns ``{"text", "char_count", "source"}``.
    """
    result = await _handle_request(request)
    return JSONResponse(content=result.model_dump())
