"""
main.py
-------
CLI entry point for the RAG Customer Support Assistant.
Run with: python main.py

✅ CHANGED: Updated banner and DB path check for FAISS
❌ REMOVED: References to ChromaDB, chroma_db directory
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.ingestion          import load_documents
from src.chunking           import chunk_documents
from src.vector_store       import build_vector_store, load_vector_store
from src.langgraph_workflow import run_assistant


# ✅ CHANGED: Updated banner — ChromaDB → FAISS
BANNER = """
╔══════════════════════════════════════════════════╗
║   RAG Customer Support Assistant                 ║
║   Powered by LangGraph + FAISS + Gemini          ║
╚══════════════════════════════════════════════════╝
Type your question. Commands: 'quit' to exit, 'rebuild' to re-ingest docs.
"""

# ✅ CHANGED: FAISS index path (was data/chroma_db)
FAISS_INDEX_DIR = "data/faiss_index"


def setup_knowledge_base(docs_path: str = "data/sample_docs") -> None:
    """Ingest PDFs and build FAISS vector store."""
    print("\n[Setup] Ingesting documents...")
    docs   = load_documents(docs_path)
    chunks = chunk_documents(docs)
    build_vector_store(chunks)
    print("[Setup] Knowledge base ready.\n")


def main():
    print(BANNER)

    # ✅ CHANGED: Check for FAISS index (not chroma_db)
    faiss_index_file = os.path.join(FAISS_INDEX_DIR, "index.faiss")
    if not os.path.exists(faiss_index_file):
        print("[Info] No FAISS index found. Building from docs...")
        setup_knowledge_base()

    print("Ready! Ask a question:\n")

    while True:
        try:
            query = input("You > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not query:
            continue

        if query.lower() == "quit":
            print("Goodbye!")
            break

        if query.lower() == "rebuild":
            setup_knowledge_base()
            continue

        result = run_assistant(query)
        print(f"\nAssistant > {result['answer']}\n")


if __name__ == "__main__":
    main()
