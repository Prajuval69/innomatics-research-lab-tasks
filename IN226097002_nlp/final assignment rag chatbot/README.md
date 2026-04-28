# RAG Customer Support Assistant — Demo-Safe (API-Free)

## ✅ What Changed (Gemini API → Deterministic Formatter)

| File | Change |
|------|--------|
| `src/rag_pipeline.py` | ❌ Removed Gemini · ✅ Added `format_answer()` + `build_sources()` + `retriever.invoke()` |
| `src/langgraph_workflow.py` | ❌ Removed `get_llm` import + `_llm` global · ✅ Updated output node to use `sources` from state |
| `requirements.txt` | ❌ Removed `google-generativeai` |

## How It Works Now

```
User Query
    ↓
FAISS Retrieval  (local, HuggingFace embeddings)
    ↓
format_answer()  (deterministic, no API)
    ↓
Structured Answer + Sources  (always succeeds)
```

## 🔧 Setup

```bash
# 1. Install dependencies (all local, no API keys needed)
pip install -r requirements.txt

# 2. Run
python main.py
```

**No `.env` file needed.** No API keys. Works fully offline after first HuggingFace model download (~90MB, cached).

## Example Output

```
Q: What is ShopEase?

A: Based on the provided document:

1. ShopEase is an online retail platform offering a wide range
   of products with fast delivery and easy returns...

2. Customers can access ShopEase via web and mobile app...

3. Support is available 24/7 via chat, email, and phone...

Sources:
  • Shopease customer support guide.pdf (Page 1)
  • Shopease customer support guide.pdf (Page 3)
```

## 📁 Project Structure

```
rag_final_project_demo/
├── main.py                   # Unchanged CLI entry point
├── requirements.txt          # ✅ Updated (no google-generativeai)
├── src/
│   ├── rag_pipeline.py       # ✅ MIGRATED — API-free formatter
│   ├── langgraph_workflow.py # ✅ UPDATED — no LLM resources
│   ├── embeddings.py         # Unchanged (HuggingFace local)
│   ├── vector_store.py       # Unchanged (FAISS)
│   ├── chunking.py           # Unchanged
│   ├── ingestion.py          # Unchanged
│   └── hitl.py               # Unchanged
├── tests/
│   └── test_queries.py
└── data/
    ├── sample_docs/
    └── faiss_index/          # Auto-created on first run
```
