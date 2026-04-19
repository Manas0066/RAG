"""
Semantic Chunker - Optimized for API-based RAG
Uses section-aware splitting + recursive chunking (fast & stable).
"""

import os
import sys
import re
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
  # (we won't use it, but keeping compatibility)


def _split_by_sections(text: str) -> List[str]:
    """Pre-split text by major section boundaries (Rules, Chapters, Parts)."""
    section_patterns = [
        r"\n(?=CHAPTER\s+[IVXLC]+)",
        r"\n(?=PART\s+[IVXLC]+)",
        r"\n(?=SCHEDULE\s+[IVXLC\d]+)",
        r"\n(?=Rule\s+\d+\.)",
        r"\n(?=\d{1,3}\.\s+[A-Z])",
    ]
    combined = "|".join(section_patterns)
    parts = re.split(combined, text)
    return [p.strip() for p in parts if len(p.strip()) > 50]


def semantic_chunk_documents(
    combined_docs: List[Dict[str, Any]],
    chunk_size: int = 500,
    chunk_overlap: int = 100,
) -> List[Document]:
    """
    Optimized chunking:
    1. Split by sections
    2. Use recursive chunking (fast + reliable)
    3. Preserve metadata
    """

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    all_chunks: List[Document] = []
    chunk_id = 0

    for doc in combined_docs:
        content = doc["content"]
        metadata = doc.get("metadata", {})

        # Keep tables as single chunk
        if metadata.get("type") == "table":
            chunk_id += 1
            all_chunks.append(Document(
                page_content=content,
                metadata={
                    **metadata,
                    "chunk_id": chunk_id,
                    "chunk_type": "table",
                },
            ))
            continue

        # Section-based splitting
        section_blocks = _split_by_sections(content)
        if not section_blocks:
            section_blocks = [content]

        for block in section_blocks:
            if len(block) < 100:
                chunk_id += 1
                all_chunks.append(Document(
                    page_content=block,
                    metadata={
                        **metadata,
                        "chunk_id": chunk_id,
                        "chunk_type": "small",
                    },
                ))
                continue

            # Recursive chunking (fast + stable)
            sub_chunks = splitter.split_text(block)

            for sc in sub_chunks:
                chunk_id += 1
                all_chunks.append(Document(
                    page_content=sc,
                    metadata={
                        **metadata,
                        "chunk_id": chunk_id,
                        "chunk_type": "text",
                    },
                ))

    print(f"[Chunker] ✓ Created {len(all_chunks)} chunks")
    return all_chunks


if __name__ == "__main__":
    from pdf_processor import process_pdf, build_combined_documents

    parsed = process_pdf()
    combined = build_combined_documents(parsed)
    chunks = semantic_chunk_documents(combined)

    print(f"\nTotal chunks: {len(chunks)}")
    for i, c in enumerate(chunks[:5]):
        print(f"\n--- Chunk {i+1} (type: {c.metadata.get('chunk_type')}, "
              f"page: {c.metadata.get('page')}) ---")
        print(c.page_content[:300])