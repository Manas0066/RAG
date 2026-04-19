"""
PDF Processor - Enhanced for Complex Tables & Structured Data
Uses pdfplumber for accurate table extraction and text parsing.
Preserves table structure as markdown for downstream processing.
Includes fallback text-pattern detection for gazette-style PDFs.
"""

import os
import sys
import re
import pdfplumber
from typing import List, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PDF_PATH


def extract_tables_from_page(page) -> List[Dict[str, Any]]:
    """Extract all tables from a single PDF page and convert to markdown."""
    tables = page.extract_tables()
    results = []
    for table in tables:
        if not table or len(table) < 2:
            continue
        # Clean cells
        cleaned = []
        for row in table:
            cleaned.append([
                (cell.strip().replace("\n", " ") if cell else "")
                for cell in row
            ])
        # Build markdown table
        headers = cleaned[0]
        md_lines = ["| " + " | ".join(headers) + " |"]
        md_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for row in cleaned[1:]:
            # Pad row if it has fewer columns than header
            while len(row) < len(headers):
                row.append("")
            md_lines.append("| " + " | ".join(row[:len(headers)]) + " |")
        md_table = "\n".join(md_lines)
        results.append({
            "type": "table",
            "content": md_table,
            "headers": headers,
            "rows": cleaned[1:],
            "num_rows": len(cleaned) - 1,
        })
    return results


def detect_text_tables(text: str) -> List[Dict[str, Any]]:
    """
    Fallback: detect tabular data embedded as plain text.
    Looks for patterns like numbered lists with structured data,
    schedule/form tables, and category definitions.
    """
    results = []

    # Pattern 1: Category / classification lists
    # e.g. "Category X—Those explosives which..."
    cat_blocks = re.findall(
        r"((?:Category|Class|Division|Group)\s+[A-Z\d]+[\s—\-:]+[^\n]+(?:\n\s+[^\n]+)*)",
        text,
        re.IGNORECASE,
    )
    if len(cat_blocks) >= 2:
        headers = ["Category", "Description"]
        rows = []
        for block in cat_blocks:
            parts = re.split(r"[\—\-:]+", block, maxsplit=1)
            if len(parts) == 2:
                rows.append([parts[0].strip(), parts[1].strip()[:300]])
        if rows:
            md_lines = ["| " + " | ".join(headers) + " |"]
            md_lines.append("| --- | --- |")
            for row in rows:
                md_lines.append("| " + " | ".join(row) + " |")
            results.append({
                "type": "table",
                "content": "\n".join(md_lines),
                "headers": headers,
                "rows": rows,
                "num_rows": len(rows),
                "detection": "text_pattern_categories",
            })

    # Pattern 2: Schedule/Form definitions with numbered items
    # e.g. "(1) Description... (2) Description..."
    schedule_match = re.search(
        r"(SCHEDULE\s+[IVXLC\d]+[^\n]*)",
        text,
        re.IGNORECASE,
    )
    if schedule_match:
        schedule_title = schedule_match.group(1).strip()
        # Find numbered items following the schedule header
        after_header = text[schedule_match.end():]
        items = re.findall(
            r"(?:^|\n)\s*\(?(\d{1,3})\)?\s*[.\-—]?\s*([^\n]+(?:\n(?!\s*\(?\d{1,3}\)?[\s.\-—])[^\n]+)*)",
            after_header,
        )
        if len(items) >= 2:
            headers = ["No.", "Description"]
            rows = [[num, desc.strip()[:300]] for num, desc in items[:20]]
            md_lines = [f"**{schedule_title}**", ""]
            md_lines.append("| " + " | ".join(headers) + " |")
            md_lines.append("| --- | --- |")
            for row in rows:
                md_lines.append("| " + " | ".join(row) + " |")
            results.append({
                "type": "table",
                "content": "\n".join(md_lines),
                "headers": headers,
                "rows": rows,
                "num_rows": len(rows),
                "detection": "text_pattern_schedule",
            })

    # Pattern 3: Quantity / distance / fee patterns
    qty_pattern = re.findall(
        r"(\d+[\d,]*\.?\d*)\s*(kg|kilogram|metre|meter|feet|km|litre|tonne)s?",
        text,
        re.IGNORECASE,
    )
    if len(qty_pattern) >= 3:
        headers = ["Value", "Unit"]
        rows = [[val, unit] for val, unit in qty_pattern[:15]]
        md_lines = ["| " + " | ".join(headers) + " |"]
        md_lines.append("| --- | --- |")
        for row in rows:
            md_lines.append("| " + " | ".join(row) + " |")
        results.append({
            "type": "table",
            "content": "\n".join(md_lines),
            "headers": headers,
            "rows": rows,
            "num_rows": len(rows),
            "detection": "text_pattern_quantities",
        })

    return results


def extract_text_from_page(page) -> str:
    """Extract clean text from a PDF page, excluding table regions."""
    # Get table bounding boxes to exclude
    tables = page.find_tables()
    table_bboxes = [t.bbox for t in tables]
    # Crop page to exclude table regions
    text_parts = []
    if table_bboxes:
        # Try to extract text from regions outside table bounding boxes
        full_text = page.extract_text() or ""
        try:
            # Extract text from each table to subtract it
            table_texts = []
            for bbox in table_bboxes:
                cropped = page.crop(bbox)
                ttext = cropped.extract_text() or ""
                if ttext.strip():
                    table_texts.append(ttext.strip())
            # Remove table text lines from full text
            filtered_text = full_text
            for ttext in table_texts:
                for line in ttext.split("\n"):
                    line = line.strip()
                    if line and line in filtered_text:
                        filtered_text = filtered_text.replace(line, "", 1)
            # Clean up excess blank lines
            import re as _re
            filtered_text = _re.sub(r"\n{3,}", "\n\n", filtered_text)
            text_parts.append(filtered_text)
        except Exception:
            # Fallback: use full text if cropping fails
            text_parts.append(full_text)
    else:
        text = page.extract_text() or ""
        text_parts.append(text)
    return "\n".join(text_parts).strip()


def detect_section_headers(text: str) -> List[Dict[str, str]]:
    """Detect section/clause headers in explosive rules text."""
    patterns = [
        # "CHAPTER I", "CHAPTER II" etc.
        r"(CHAPTER\s+[IVXLC]+[.\s]*.*)",
        # "PART I", "PART II" etc.
        r"(PART\s+[IVXLC]+[.\s]*.*)",
        # Numbered sections like "1.", "2.", "12."
        r"^(\d{1,3}\.\s+[A-Z].*)",
        # Subsections like "(a)", "(b)", "(1)", "(2)"
        r"^(\(\d+\)\s+.*)",
        r"^(\([a-z]\)\s+.*)",
        # "Rule 1", "Rule 2" etc.
        r"(Rule\s+\d+[.\s]*.*)",
        # "Schedule" patterns
        r"(SCHEDULE\s+[IVXLC\d]+.*)",
        # "Form" patterns
        r"(FORM\s+[A-Z\-\d]+.*)",
    ]
    headers = []
    for line in text.split("\n"):
        line_stripped = line.strip()
        for pat in patterns:
            match = re.match(pat, line_stripped, re.IGNORECASE)
            if match:
                headers.append({
                    "text": match.group(1).strip(),
                    "full_line": line_stripped,
                })
                break
    return headers


def process_pdf(pdf_path: str = None) -> Dict[str, Any]:
    if pdf_path is None:
        from config import PDF_PATH
        pdf_path = PDF_PATH

    """
    Process the PDF file completely.
    Returns structured data with pages, text blocks, tables, and sections.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    print(f"[PDF Processor] Loading: {pdf_path}")
    all_pages = []
    all_tables = []
    all_text = []
    all_sections = []

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"[PDF Processor] Total pages: {total_pages}")

        for i, page in enumerate(pdf.pages):
            page_num = i + 1

            # Extract text
            text = extract_text_from_page(page)
            if text:
                all_text.append({
                    "page": page_num,
                    "content": text,
                })
                # Detect section headers
                headers = detect_section_headers(text)
                for h in headers:
                    h["page"] = page_num
                    all_sections.append(h)

            # Extract tables (pdfplumber structural detection)
            tables = extract_tables_from_page(page)

            # Fallback: detect text-based tabular patterns if no structural tables found
            if not tables and text:
                text_tables = detect_text_tables(text)
                tables.extend(text_tables)

            for t in tables:
                t["page"] = page_num
                all_tables.append(t)

            all_pages.append({
                "page": page_num,
                "text": text,
                "tables": tables,
            })

            if (page_num) % 20 == 0:
                print(f"[PDF Processor] Processed {page_num}/{total_pages} pages...")

    print(f"[PDF Processor] ✓ Extracted {len(all_text)} text blocks, "
          f"{len(all_tables)} tables, {len(all_sections)} section headers")

    return {
        "pages": all_pages,
        "text_blocks": all_text,
        "tables": all_tables,
        "sections": all_sections,
        "total_pages": total_pages,
        "source": pdf_path,
    }


def build_combined_documents(parsed_data: Dict) -> List[Dict[str, Any]]:
    """
    Combine text and tables into unified document blocks per page.
    Tables are embedded as markdown within page text for context.
    """
    documents = []
    for page_data in parsed_data["pages"]:
        page_num = page_data["page"]
        text = page_data["text"] or ""
        tables = page_data["tables"]

        # Build combined content
        combined = text
        if tables:
            combined += "\n\n"
            for idx, t in enumerate(tables):
                combined += f"\n[TABLE {idx+1} on Page {page_num}]\n"
                combined += t["content"]
                combined += "\n"

        if combined.strip():
            documents.append({
                "content": combined.strip(),
                "metadata": {
                    "page": page_num,
                    "source": parsed_data["source"],
                    "has_tables": len(tables) > 0,
                    "num_tables": len(tables),
                },
            })

    # Also create standalone table documents for retrieval assurance
    for t in parsed_data["tables"]:
        table_doc = (
            f"[TABLE - Page {t['page']}]\n"
            f"Headers: {', '.join(t['headers'])}\n"
            f"{t['content']}"
        )
        documents.append({
            "content": table_doc,
            "metadata": {
                "page": t["page"],
                "source": parsed_data["source"],
                "type": "table",
                "headers": ", ".join(t["headers"]),
                "num_rows": t["num_rows"],
            },
        })

    print(f"[PDF Processor] ✓ Built {len(documents)} combined documents")
    return documents


if __name__ == "__main__":
    parsed = process_pdf()
    docs = build_combined_documents(parsed)

    print(f"\n--- Sample Text Block (Page 1) ---")
    if parsed["text_blocks"]:
        print(parsed["text_blocks"][0]["content"][:500])

    print(f"\n--- Sample Table ---")
    if parsed["tables"]:
        print(parsed["tables"][0]["content"][:500])

    print(f"\n--- Sections Found ---")
    for s in parsed["sections"][:10]:
        print(f"  Page {s['page']}: {s['text'][:80]}")
