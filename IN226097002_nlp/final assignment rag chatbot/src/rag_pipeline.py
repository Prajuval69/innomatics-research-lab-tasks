"""
rag_pipeline.py
---------------
DEMO-SAFE RAG Pipeline — No external API required.

Flow:
  User Query
      ↓
  FAISS Retrieval  (HuggingFace embeddings, fully local)
      ↓
  Structured Answer Formatter  (deterministic, never fails)
      ↓
  Clean Answer + Sources

✅ ADDED: deterministic answer formatter (format_answer)
✅ ADDED: retriever.invoke() — replaces deprecated get_relevant_documents()
✅ ADDED: source citation builder
❌ REMOVED: google.generativeai import
❌ REMOVED: genai.configure(), get_llm(), generate_with_gemini()
❌ REMOVED: GEMINI_API_KEY usage
❌ REMOVED: PromptTemplate (no longer needed)
❌ REMOVED: rate-limit / auth error messages
"""

import os
from typing import Any, Dict, List

from langchain.schema import Document

from vector_store import load_vector_store, get_retriever

# ── Config ──────────────────────────────────────────────
TOP_K = 3   # Number of chunks to retrieve and display
# ────────────────────────────────────────────────────────


# ── Low-confidence detection ───────────────────────────
# Kept for HITL escalation compatibility — still useful
# even without an LLM (e.g. "no chunks found" = low confidence)
LOW_CONFIDENCE_PHRASES = [
    "no relevant information",
    "please enter a valid question",
]
# ────────────────────────────────────────────────────────


def format_answer(chunks: List[Document]) -> str:
    """
    ✅ NEW: Build a clean, structured answer from retrieved chunks.
    Completely deterministic — no API, no randomness, never fails.

    Format:
        Based on the provided document:

        1. <chunk 1 text>

        2. <chunk 2 text>

        3. <chunk 3 text>
    """
    answer = "Based on the provided document:\n\n"
    for i, doc in enumerate(chunks[:TOP_K], 1):
        text = doc.page_content.strip()
        # Truncate very long chunks for clean display (max 400 chars)
        if len(text) > 400:
            text = text[:400].rsplit(" ", 1)[0] + "..."
        answer += f"{i}. {text}\n\n"
    return answer.strip()


def build_sources(chunks: List[Document]) -> List[str]:
    """
    ✅ NEW: Extract unique, human-readable source citations from chunks.

    Example output:
        ["Shopease customer support guide.pdf (Page 2)",
         "Shopease customer support guide.pdf (Page 5)"]
    """
    seen   = set()
    result = []
    for chunk in chunks[:TOP_K]:
        src  = os.path.basename(chunk.metadata.get("source", "Unknown document"))
        page = chunk.metadata.get("page", "?")
        label = f"{src} (Page {page})"
        if label not in seen:
            seen.add(label)
            result.append(label)
    return result


def is_low_confidence(answer: str) -> bool:
    """Check if answer signals low confidence (no chunks found)."""
    lower = answer.lower()
    return any(phrase in lower for phrase in LOW_CONFIDENCE_PHRASES)


def run_rag(query: str, retriever, llm=None) -> Dict[str, Any]:
    """
    Execute the demo-safe RAG pipeline for a given query.

    Parameters:
        query     : user question string
        retriever : FAISS retriever (from get_retriever())
        llm       : ignored — kept for signature compatibility with workflow

    Returns:
        {
            "query"         : original question,
            "answer"        : structured answer string,
            "source_chunks" : list of retrieved Document objects,
            "sources"       : list of human-readable source strings,
            "low_confidence": bool
        }
    """
    # ── Guard: empty query ─────────────────────────────
    if not query or not query.strip():
        return {
            "query"         : query,
            "answer"        : "Please enter a valid question.",
            "source_chunks" : [],
            "sources"       : [],
            "low_confidence": True,
        }

    # ── Step 1: Retrieve relevant chunks ──────────────
    # ✅ CHANGED: .invoke() replaces deprecated .get_relevant_documents()
    try:
        chunks: List[Document] = retriever.invoke(query)
    except Exception as e:
        print(f"[RAG] Retrieval error: {e}")
        chunks = []

    # ── Step 2: Guard — no results ────────────────────
    if not chunks:
        return {
            "query"         : query,
            "answer"        : "No relevant information found in the document.",
            "source_chunks" : [],
            "sources"       : [],
            "low_confidence": True,
        }

    # ── Step 3: Build structured answer ───────────────
    # ✅ NEW: deterministic formatter — no API call needed
    answer  = format_answer(chunks)
    sources = build_sources(chunks)

    return {
        "query"         : query,
        "answer"        : answer,
        "source_chunks" : chunks,
        "sources"       : sources,
        "low_confidence": False,
    }


# ── Standalone test ────────────────────────────────────
if __name__ == "__main__":
    store   = load_vector_store()
    retrvr  = get_retriever(store)

    queries = [
        "What is ShopEase?",
        "What is the return policy?",
        "How do I track my order?",
    ]

    for q in queries:
        print(f"\n{'='*60}")
        result = run_rag(q, retrvr)

        print(f"Q: {result['query']}")
        print(f"\nA: {result['answer']}")

        if result["sources"]:
            print("Sources:")
            for s in result["sources"]:
                print(f"  • {s}")

        print(f"Low confidence: {result['low_confidence']}")
