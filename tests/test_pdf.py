"""Tests for PDF text extraction utility."""

from __future__ import annotations

from typing import TYPE_CHECKING

import fitz
import pytest

from meridian.common.pdf import extract_text_from_pdf

if TYPE_CHECKING:
    from pathlib import Path


def _create_test_pdf(text: str, path: Path) -> None:
    """Create a minimal PDF with the given text content."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text, fontsize=12)
    doc.save(str(path))
    doc.close()


def _create_multi_page_pdf(pages: list[str], path: Path) -> None:
    """Create a multi-page PDF with one text block per page."""
    doc = fitz.open()
    for text in pages:
        page = doc.new_page()
        page.insert_text((72, 72), text, fontsize=12)
    doc.save(str(path))
    doc.close()


class TestExtractFromPath:
    """Tests for extraction from file paths."""

    def test_single_page_pdf(self, tmp_path: Path) -> None:
        """Single-page PDF returns its text content."""
        pdf_path = tmp_path / "test.pdf"
        _create_test_pdf("Chief Technology Officer at BMW Group", pdf_path)

        result = extract_text_from_pdf(pdf_path)
        assert "Chief Technology Officer" in result
        assert "BMW Group" in result

    def test_multi_page_pdf(self, tmp_path: Path) -> None:
        """Multi-page PDF concatenates text from all pages."""
        pdf_path = tmp_path / "multi.pdf"
        _create_multi_page_pdf(
            ["Page one: Requirements", "Page two: Qualifications", "Page three: Benefits"],
            pdf_path,
        )

        result = extract_text_from_pdf(pdf_path)
        assert "Page one" in result
        assert "Page two" in result
        assert "Page three" in result

    def test_string_path(self, tmp_path: Path) -> None:
        """String path works the same as Path object."""
        pdf_path = tmp_path / "str_path.pdf"
        _create_test_pdf("String path test", pdf_path)

        result = extract_text_from_pdf(str(pdf_path))
        assert "String path test" in result

    def test_nonexistent_file_raises(self) -> None:
        """Non-existent file path raises ValueError."""
        with pytest.raises(ValueError, match="Failed to open PDF"):
            extract_text_from_pdf("/nonexistent/path/file.pdf")

    def test_empty_pdf_returns_empty_string(self, tmp_path: Path) -> None:
        """PDF with no text content returns empty string."""
        pdf_path = tmp_path / "empty.pdf"
        doc = fitz.open()
        doc.new_page()  # blank page
        doc.save(str(pdf_path))
        doc.close()

        result = extract_text_from_pdf(pdf_path)
        assert result == ""


class TestExtractFromBytes:
    """Tests for extraction from raw bytes."""

    def test_bytes_input(self, tmp_path: Path) -> None:
        """Raw PDF bytes are extracted correctly."""
        pdf_path = tmp_path / "bytes_test.pdf"
        _create_test_pdf("Bytes extraction test", pdf_path)
        pdf_bytes = pdf_path.read_bytes()

        result = extract_text_from_pdf(pdf_bytes)
        assert "Bytes extraction test" in result

    def test_invalid_bytes_raises(self) -> None:
        """Non-PDF bytes raise ValueError."""
        with pytest.raises(ValueError, match="Failed to open PDF"):
            extract_text_from_pdf(b"this is not a pdf")


class TestContentPreservation:
    """Tests that extracted text preserves content accuracy."""

    def test_numbers_preserved(self, tmp_path: Path) -> None:
        """Numerical values in PDF are extracted accurately."""
        pdf_path = tmp_path / "numbers.pdf"
        _create_test_pdf("P&L responsibility of USD 500M+ across 3 regions", pdf_path)

        result = extract_text_from_pdf(pdf_path)
        assert "500M" in result
        assert "3 regions" in result

    def test_special_characters(self, tmp_path: Path) -> None:
        """Common CV/JD special characters survive extraction."""
        pdf_path = tmp_path / "special.pdf"
        _create_test_pdf("10+ years experience (2014-2024)", pdf_path)

        result = extract_text_from_pdf(pdf_path)
        assert "10+" in result
        assert "2014" in result
        assert "2024" in result
