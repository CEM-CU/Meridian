"""Tests for the /api/upload/jd and /api/upload/cv endpoints."""

from __future__ import annotations

import io

import pytest
from httpx import ASGITransport, AsyncClient

from meridian.api.app import app

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BASE = "http://test"
_SAMPLE_TEXT = "We are seeking a Chief Executive Officer with 15 years of experience."


async def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url=_BASE)


# ---------------------------------------------------------------------------
# /api/upload/jd — JSON (paste) body
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upload_jd_paste_returns_200() -> None:
    """POST /api/upload/jd with JSON body returns 200."""
    async with await _client() as client:
        response = await client.post("/api/upload/jd", json={"text": _SAMPLE_TEXT})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_upload_jd_paste_response_fields() -> None:
    """Response contains text, char_count, and source='paste'."""
    async with await _client() as client:
        response = await client.post("/api/upload/jd", json={"text": _SAMPLE_TEXT})
    data = response.json()
    assert "text" in data
    assert "char_count" in data
    assert "source" in data
    assert data["source"] == "paste"
    assert data["text"] == _SAMPLE_TEXT.strip()
    assert data["char_count"] == len(_SAMPLE_TEXT.strip())


@pytest.mark.asyncio
async def test_upload_jd_empty_text_returns_400() -> None:
    """POST /api/upload/jd with empty text returns 400."""
    async with await _client() as client:
        response = await client.post("/api/upload/jd", json={"text": "   "})
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# /api/upload/cv — JSON (paste) body
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upload_cv_paste_returns_200() -> None:
    """POST /api/upload/cv with JSON body returns 200."""
    cv_text = "Jane Doe — Chief Financial Officer — 20 years in finance."
    async with await _client() as client:
        response = await client.post("/api/upload/cv", json={"text": cv_text})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_upload_cv_paste_response_fields() -> None:
    """CV response contains text, char_count, and source='paste'."""
    cv_text = "Jane Doe — Chief Financial Officer — 20 years in finance."
    async with await _client() as client:
        response = await client.post("/api/upload/cv", json={"text": cv_text})
    data = response.json()
    assert data["source"] == "paste"
    assert data["char_count"] == len(cv_text.strip())


@pytest.mark.asyncio
async def test_upload_cv_empty_text_returns_400() -> None:
    """POST /api/upload/cv with empty text returns 400."""
    async with await _client() as client:
        response = await client.post("/api/upload/cv", json={"text": ""})
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# File upload — plain-text multipart
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upload_jd_text_file_returns_200() -> None:
    """POST /api/upload/jd with a plain-text file returns 200 and source='text'."""
    content = b"Looking for a visionary CTO with deep engineering background."
    async with await _client() as client:
        response = await client.post(
            "/api/upload/jd",
            files={"file": ("jd.txt", io.BytesIO(content), "text/plain")},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "text"
    assert data["text"] == content.decode("utf-8").strip()


@pytest.mark.asyncio
async def test_upload_cv_text_file_response_fields() -> None:
    """CV text-file upload response has all required fields."""
    content = b"John Smith - VP Engineering - 12 years experience."
    async with await _client() as client:
        response = await client.post(
            "/api/upload/cv",
            files={"file": ("cv.txt", io.BytesIO(content), "text/plain")},
        )
    data = response.json()
    assert "text" in data
    assert "char_count" in data
    assert "source" in data
    assert data["source"] == "text"
