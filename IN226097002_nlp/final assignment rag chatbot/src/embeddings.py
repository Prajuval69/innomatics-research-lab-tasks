"""
embeddings.py
-------------
Wraps HuggingFace sentence-transformers embedding model.
Default: all-MiniLM-L6-v2 (lightweight, fast, good quality).
Swap model_name for a stronger model if accuracy needed.
"""

from langchain_community.embeddings import HuggingFaceEmbeddings


# ── Config ──────────────────────────────────────────────
MODEL_NAME   = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_KWARGS = {"device": "cpu"}   # change to "cuda" if GPU available
ENCODE_KWARGS = {"normalize_embeddings": True}
# ────────────────────────────────────────────────────────


def get_embedding_model() -> HuggingFaceEmbeddings:
    """
    Load and return embedding model.
    First call downloads model (~90 MB). Cached locally after that.
    """
    print(f"[Embeddings] Loading model: {MODEL_NAME}")
    embeddings = HuggingFaceEmbeddings(
        model_name=MODEL_NAME,
        model_kwargs=MODEL_KWARGS,
        encode_kwargs=ENCODE_KWARGS,
    )
    print("[Embeddings] Model ready.")
    return embeddings


if __name__ == "__main__":
    model = get_embedding_model()
    test  = model.embed_query("What is the refund policy?")
    print(f"[Embeddings] Test vector dim: {len(test)}")
    print(f"[Embeddings] Sample values  : {test[:5]}")
