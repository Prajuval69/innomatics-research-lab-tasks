"""
chunking.py
-----------
Splits raw documents into overlapping chunks.
Chunk size = 500 tokens, overlap = 50 tokens.
Overlap preserves context at chunk boundaries.
"""

from typing import List
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter


# ── Config ──────────────────────────────────────────────
CHUNK_SIZE    = 500   # characters per chunk
CHUNK_OVERLAP = 50    # characters overlap between chunks
# ────────────────────────────────────────────────────────


def chunk_documents(documents: List[Document]) -> List[Document]:
    """
    Split documents into smaller chunks for embedding.

    Uses RecursiveCharacterTextSplitter which tries to split
    on paragraphs → sentences → words → characters (in order).
    This keeps semantic units together whenever possible.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )

    chunks = splitter.split_documents(documents)

    print(f"[Chunking] {len(documents)} pages → {len(chunks)} chunks")
    print(f"           chunk_size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP}")

    return chunks


def preview_chunks(chunks: List[Document], n: int = 3) -> None:
    """Print first n chunks for inspection."""
    for i, chunk in enumerate(chunks[:n]):
        print(f"\n── Chunk {i+1} ──")
        print(f"  Source : {chunk.metadata.get('source', 'unknown')}")
        print(f"  Page   : {chunk.metadata.get('page', 'N/A')}")
        print(f"  Length : {len(chunk.page_content)} chars")
        print(f"  Preview: {chunk.page_content[:120]}...")


if __name__ == "__main__":
    from ingestion import load_documents
    docs   = load_documents("data/sample_docs")
    chunks = chunk_documents(docs)
    preview_chunks(chunks)
