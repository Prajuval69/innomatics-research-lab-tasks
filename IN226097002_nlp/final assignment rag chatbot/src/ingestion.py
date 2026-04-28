"""
ingestion.py
------------
Loads PDF documents and prepares them for the RAG pipeline.
Handles single files and entire directories.
"""

import os
from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.schema import Document


def load_pdf(file_path: str) -> List[Document]:
    """Load a single PDF file and return list of LangChain Document objects."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF not found: {file_path}")

    loader = PyPDFLoader(file_path)
    documents = loader.load()

    print(f"[Ingestion] Loaded {len(documents)} pages from: {file_path}")
    return documents


def load_directory(dir_path: str) -> List[Document]:
    """Load all PDFs from a directory."""
    if not os.path.isdir(dir_path):
        raise NotADirectoryError(f"Directory not found: {dir_path}")

    loader = DirectoryLoader(
        dir_path,
        glob="**/*.pdf",
        loader_cls=PyPDFLoader,
        show_progress=True
    )
    documents = loader.load()

    print(f"[Ingestion] Loaded {len(documents)} total pages from: {dir_path}")
    return documents


def load_documents(path: str) -> List[Document]:
    """Smart loader - detects file vs directory automatically."""
    p = Path(path)
    if p.is_file() and p.suffix.lower() == ".pdf":
        return load_pdf(path)
    elif p.is_dir():
        return load_directory(path)
    else:
        raise ValueError(f"Path must be a PDF file or directory: {path}")


if __name__ == "__main__":
    # Quick test
    docs = load_documents("data/sample_docs")
    for doc in docs[:2]:
        print(f"  Source: {doc.metadata.get('source', 'unknown')}")
        print(f"  Page:   {doc.metadata.get('page', 'N/A')}")
        print(f"  Chars:  {len(doc.page_content)}")
        print()
