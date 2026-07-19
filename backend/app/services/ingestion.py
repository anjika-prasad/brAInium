"""
Document -> plain text extraction.

Strategy:
1. Try Docling first -- it handles digital PDFs, tables, and layout
   structure well and is far cheaper than OCR.
2. If Docling returns near-empty text (a strong signal the PDF is a
   scanned image with no text layer -- common for old inspection
   reports and hand-filled forms), fall back to PaddleOCR page by page.

This two-tier approach keeps ingestion fast for the ~80% of documents
that are already digital, and only pays the OCR cost where needed.
"""
from dataclasses import dataclass
from pathlib import Path

MIN_CHARS_PER_PAGE_THRESHOLD = 40  # below this, assume the page is a scanned image


@dataclass
class ParsedPage:
    page_number: int
    text: str
    used_ocr: bool


@dataclass
class ParsedDocument:
    filename: str
    pages: list[ParsedPage]

    @property
    def full_text(self) -> str:
        return "\n\n".join(p.text for p in self.pages)


def _parse_with_docling(path: Path) -> list[ParsedPage]:
    from docling.document_converter import DocumentConverter

    converter = DocumentConverter()
    result = converter.convert(str(path))
    doc = result.document

    pages: list[ParsedPage] = []
    # Docling exposes per-page text via export; group markdown export by page break markers.
    md = doc.export_to_markdown()
    # Docling doesn't always give hard page breaks in markdown -- fall back to
    # treating the whole doc as "page 1" if page-level splitting isn't available.
    page_texts = md.split("\f") if "\f" in md else [md]
    for i, text in enumerate(page_texts, start=1):
        pages.append(ParsedPage(page_number=i, text=text.strip(), used_ocr=False))
    return pages


def _parse_with_paddleocr(path: Path) -> list[ParsedPage]:
    from paddleocr import PaddleOCR
    from pdf2image import convert_from_path

    ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
    images = convert_from_path(str(path), dpi=300)

    pages: list[ParsedPage] = []
    for i, image in enumerate(images, start=1):
        result = ocr.ocr(_pil_to_ndarray(image), cls=True)
        lines = []
        for block in result or []:
            for _, (text, _confidence) in block:
                lines.append(text)
        pages.append(ParsedPage(page_number=i, text="\n".join(lines), used_ocr=True))
    return pages


def _pil_to_ndarray(image):
    import numpy as np
    return np.array(image)


def parse_document(path: Path) -> ParsedDocument:
    pages = _parse_with_docling(path)

    needs_ocr = any(len(p.text) < MIN_CHARS_PER_PAGE_THRESHOLD for p in pages)
    if needs_ocr:
        try:
            ocr_pages = _parse_with_paddleocr(path)
            # Merge: prefer Docling text where it had enough content, else OCR
            merged = []
            for i, docling_page in enumerate(pages):
                if len(docling_page.text) >= MIN_CHARS_PER_PAGE_THRESHOLD or i >= len(ocr_pages):
                    merged.append(docling_page)
                else:
                    merged.append(ocr_pages[i])
            pages = merged
        except Exception:
            # OCR is a best-effort enhancement -- never let it fail ingestion outright.
            pass

    return ParsedDocument(filename=path.name, pages=pages)
