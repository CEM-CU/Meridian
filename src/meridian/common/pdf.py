"""PDF text extraction utility.

Extracts text content from PDF files using PyMuPDF (fitz).
Text-only extraction — no OCR. Accepts file paths or raw bytes.
"""

from __future__ import annotations

import logging
from pathlib import Path

import fitz

logger = logging.getLogger(__name__)


def extract_text_from_pdf(source: str | Path | bytes) -> str:
    """Extract all text from a PDF document.

    Args:
        source: One of:
            - A file path (str or Path) to a PDF on disk.
            - Raw PDF bytes (e.g., from an upload or HTTP response).

    Returns:
        Concatenated text from all pages, separated by newlines.
        Returns an empty string if the PDF contains no extractable text.

    Raises:
        FileNotFoundError: If a file path is provided but does not exist.
        ValueError: If the source cannot be opened as a PDF.
    """
    try:
        doc = _open_document(source)
    except Exception as exc:
        raise ValueError(f"Failed to open PDF: {exc}") from exc

    try:
        pages: list[str] = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            text: str = str(page.get_text())
            if text.strip():
                pages.append(text)

        result = "\n".join(pages)
        logger.info(
            "PDF text extraction complete: pages=%d, chars=%d",
            len(doc),
            len(result),
        )
        return result
    finally:
        doc.close()


def _open_document(source: str | Path | bytes) -> fitz.Document:
    """Open a PDF from a file path or raw bytes."""
    if isinstance(source, bytes):
        return fitz.open(stream=source, filetype="pdf")

    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")
    return fitz.open(str(path))
