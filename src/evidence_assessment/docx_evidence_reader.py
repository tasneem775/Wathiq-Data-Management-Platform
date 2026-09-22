"""DOCX Evidence Reader.

Reads a single Word (.docx) evidence file and extracts the information
needed later by the Gap Analysis Engine, Supporting Evidence Detector,
Recommendation Engine, Word Report Generator, and Dashboard.

This module does not analyze images and does not use OCR. It only
extracts paragraph/table text and reports how many images exist and
their basic metadata (file name, extension, size in bytes).

No LLM, no OpenAI/OpenRouter, no LangChain, no OCR, no external API is
used here. Only python-docx, zipfile, pathlib, and the standard library.
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path
from typing import Any

from docx import Document
from docx.document import Document as DocumentObject
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

SUPPORTED_EXTENSION = ".docx"


def _iter_block_items(document: DocumentObject):
    """Yield Paragraph and Table objects in the order they appear in the document body."""
    body = document.element.body
    for child in body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, document)
        elif child.tag == qn("w:tbl"):
            yield Table(child, document)


def _read_images_from_zip(file_path: Path) -> list[dict[str, Any]]:
    """Read image metadata from the word/media/ folder inside the .docx (as a ZIP)."""
    image_files: list[dict[str, Any]] = []
    with zipfile.ZipFile(file_path) as archive:
        for info in archive.infolist():
            if info.filename.startswith("word/media/") and not info.is_dir():
                name = Path(info.filename).name
                if not name:
                    continue
                image_files.append(
                    {
                        "file_name": name,
                        "extension": Path(name).suffix.lower(),
                        "size_bytes": info.file_size,
                    }
                )
    return image_files


def read_docx_evidence(file_path: str) -> dict[str, Any]:
    """Read a single .docx evidence file and extract text, tables, and image metadata.

    Args:
        file_path: Path to the .docx evidence file.

    Returns:
        A dictionary describing the read result. See module docstring for the
        list of keys. Errors are never raised to the caller; they are reported
        via read_status = "read_error" and a message in warnings.
    """
    path = Path(file_path)
    result: dict[str, Any] = {
        "file_path": str(file_path),
        "file_name": path.name,
        "file_extension": path.suffix,
        "read_status": "success",
        "text": "",
        "text_length": 0,
        "paragraphs_count": 0,
        "tables_count": 0,
        "table_rows_count": 0,
        "images_count": 0,
        "image_files": [],
        "warnings": [],
    }

    if not path.exists():
        result["read_status"] = "file_not_found"
        result["warnings"].append(f"File not found: {file_path}")
        return result

    if path.suffix.lower() != SUPPORTED_EXTENSION:
        result["read_status"] = "unsupported_file_type"
        result["warnings"].append(f"Unsupported file extension: {path.suffix}")
        return result

    try:
        document = Document(str(path))

        lines: list[str] = []
        paragraphs_count = 0
        tables_count = 0
        table_rows_count = 0

        for block in _iter_block_items(document):
            if isinstance(block, Paragraph):
                text = block.text.strip()
                if text:
                    lines.append(text)
                    paragraphs_count += 1
            elif isinstance(block, Table):
                tables_count += 1
                for row in block.rows:
                    table_rows_count += 1
                    cells_text = [cell.text.strip() for cell in row.cells]
                    lines.append(" | ".join(cells_text))

        image_files = _read_images_from_zip(path)

        result["text"] = "\n".join(lines)
        result["text_length"] = len(result["text"])
        result["paragraphs_count"] = paragraphs_count
        result["tables_count"] = tables_count
        result["table_rows_count"] = table_rows_count
        result["images_count"] = len(image_files)
        result["image_files"] = image_files
    except Exception as error:  # noqa: BLE001 - errors must be reported, not raised
        result["read_status"] = "read_error"
        result["text"] = ""
        result["warnings"].append(f"Failed to read DOCX file: {error}")

    return result


def get_docx_reader_capabilities() -> dict[str, Any]:
    """Return the capabilities of this DOCX evidence reader."""
    return {
        "supported_extensions": [SUPPORTED_EXTENSION],
        "extracts_paragraphs": True,
        "extracts_tables": True,
        "detects_images": True,
        "uses_ocr": False,
        "analyzes_images": False,
    }


def main() -> None:
    """Command-line entry point.

    Usage:
        python -m src.evidence_assessment.docx_evidence_reader "path/to/file.docx"
    """
    if len(sys.argv) < 2:
        print("ضع مسار ملف DOCX لاختبار القراءة.")
        return

    file_path = sys.argv[1]
    result = read_docx_evidence(file_path)

    lines = [
        f"read_status: {result['read_status']}",
        f"file_name: {result['file_name']}",
        f"paragraphs_count: {result['paragraphs_count']}",
        f"tables_count: {result['tables_count']}",
        f"table_rows_count: {result['table_rows_count']}",
        f"images_count: {result['images_count']}",
        f"text_length: {result['text_length']}",
        f"text[:500]: {result['text'][:500]}",
        f"warnings: {result['warnings']}",
    ]
    for line in lines:
        try:
            print(line)
        except UnicodeEncodeError:
            encoding = sys.stdout.encoding or "utf-8"
            print(line.encode(encoding, errors="replace").decode(encoding))


if __name__ == "__main__":
    main()
