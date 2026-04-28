"""
vector_store.py
---------------
Manages FAISS vector store.
Supports: build, save, load, and query operations.

✅ CHANGED: ChromaDB → FAISS (local, fast, no server needed)
❌ REMOVED: Chroma, chromadb, collection_name, persist()
✅ ADDED:   FAISS.from_documents(), save_local(), load_local()

FAISS advantages over ChromaDB:
  - Faster similarity search (C++ optimised)
  - No external DB process required
  - Industry-standard (used at Meta/Google scale)
  - Fully offline
"""

import os
from typing import List, Optional

# ✅ CHANGED: Import FAISS instead of Chroma
from langchain_community.vectorstores import FAISS
from langchain.schema import Document

from embeddings import get_embedding_model


# ── Config ──────────────────────────────────────────────
# ✅ CHANGED: FAISS saves as a folder with two files (index.faiss + index.pkl)
FAISS_INDEX_DIR = "data/faiss_index"
# ────────────────────────────────────────────────────────


def build_vector_store(chunks: List[Document]) -> FAISS:
    """
    Embed chunks and store in FAISS index.
    ✅ CHANGED: Chroma.from_documents() → FAISS.from_documents()
    ✅ CHANGED: persist() → save_local()
    """
    if not chunks:
        raise ValueError("[VectorStore] No chunks provided. Ingest documents first.")

    embeddings = get_embedding_model()

    print(f"[VectorStore] Building FAISS index with {len(chunks)} chunks...")

    # ✅ CHANGED: Build FAISS index from documents
    vector_store = FAISS.from_documents(
        documents=chunks,
        embedding=embeddings,
    )

    # ✅ CHANGED: save_local() replaces persist()
    os.makedirs(FAISS_INDEX_DIR, exist_ok=True)
    vector_store.save_local(FAISS_INDEX_DIR)
    print(f"[VectorStore] Saved FAISS index to: {FAISS_INDEX_DIR}")

    return vector_store


def load_vector_store() -> Optional[FAISS]:
    """
    Load existing FAISS index from disk.
    ✅ CHANGED: Chroma() constructor → FAISS.load_local()
    Returns None if index doesn't exist yet.
    """
    index_file = os.path.join(FAISS_INDEX_DIR, "index.faiss")

    if not os.path.exists(index_file):
        print("[VectorStore] No existing FAISS index found. Run build first.")
        return None

    embeddings = get_embedding_model()

    # ✅ CHANGED: Load via FAISS.load_local()
    # allow_dangerous_deserialization=True needed for LangChain FAISS loader
    vector_store = FAISS.load_local(
        folder_path=FAISS_INDEX_DIR,
        embeddings=embeddings,
        allow_dangerous_deserialization=True,
    )
    print(f"[VectorStore] Loaded FAISS index from: {FAISS_INDEX_DIR}")
    return vector_store


def get_retriever(vector_store: FAISS, k: int = 5):
    """
    Return a retriever that fetches top-k similar chunks.
    ✅ IMPROVED: k=5 (up from 4) for better retrieval coverage.
    FAISS MMR (Maximal Marginal Relevance) available for diversity:
      use search_type="mmr" to reduce redundant chunks.
    """
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    )


if __name__ == "__main__":
    from ingestion import load_documents
    from chunking   import chunk_documents

    docs    = load_documents("data/sample_docs")
    chunks  = chunk_documents(docs)
    store   = build_vector_store(chunks)
    retrvr  = get_retriever(store)

    results = retrvr.get_relevant_documents("How do I reset my password?")
    print(f"\n[Test] Top results for 'reset password':")
    for i, r in enumerate(results):
        print(f"  [{i+1}] {r.page_content[:100]}...")
