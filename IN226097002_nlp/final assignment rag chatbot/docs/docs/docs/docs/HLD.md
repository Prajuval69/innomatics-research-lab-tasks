# HIGH-LEVEL DESIGN (HLD)
## RAG-Based Customer Support Assistant with LangGraph & HITL
**Project:** Innomatics Research Labs — Mandatory Internship Project
**Version:** 1.0 | **Author:** [Your Name]

---

## 1. System Overview

### Problem Definition
Customer support teams face high query volumes with repetitive, document-based questions (return policies, shipping, billing). Human agents waste time on FAQs instead of complex cases. Generic chatbots hallucinate answers not in the knowledge base.

**This system solves it by:**
- Grounding answers strictly in company knowledge base (PDFs)
- Automatically routing uncertain queries to human agents
- Never fabricating information — "I don't know" beats wrong answers

### Scope
| In Scope | Out of Scope |
|---|---|
| PDF document ingestion | Real-time web browsing |
| Semantic search over docs | Multi-language support |
| LLM-powered answer generation | Voice interface |
| Intent-based routing | CRM system integration |
| Human escalation simulation | Production deployment |
| CLI interaction | Mobile app |

---

## 2. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        OFFLINE: INGESTION PIPELINE                  │
│                                                                     │
│  [PDF Files] → [Document Loader] → [Text Splitter] → [Embeddings]  │
│                                                               ↓     │
│                                                    [ChromaDB Vector │
│                                                       Database]     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        ONLINE: QUERY PIPELINE                       │
│                                                                     │
│  [User / CLI]                                                       │
│      ↓                                                              │
│  ┌───────────┐                                                      │
│  │   INPUT   │  ← Validate & clean query                           │
│  │   NODE    │                                                      │
│  └─────┬─────┘                                                      │
│        ↓                                                            │
│  ┌───────────┐       ┌──────────────┐                              │
│  │ RETRIEVAL │──────►│  ChromaDB    │  Top-K similar chunks        │
│  │   NODE    │◄──────│  Vector DB   │                              │
│  └─────┬─────┘       └──────────────┘                              │
│        ↓                                                            │
│  ┌───────────┐       ┌──────────────┐                              │
│  │GENERATION │──────►│     LLM      │  Mistral / GPT-3.5           │
│  │   NODE    │◄──────│  (via Ollama)│                              │
│  └─────┬─────┘       └──────────────┘                              │
│        ↓                                                            │
│   [ROUTER / CONDITIONAL EDGE]                                       │
│       / \\                                                           │
│      /   \\                                                          │
│     ↓     ↓                                                         │
│  [HITL] [OUTPUT]                                                    │
│    ↓        ↓                                                       │
│ [Human   [Final                                                     │
│  Agent]  Answer]                                                    │
└─────────────────────────────────────────────────────────────────────┘

         Powered by LangGraph StateGraph
```

---

## 3. Component Descriptions

### 3.1 Document Loader (`ingestion.py`)
- Uses `PyPDFLoader` from LangChain
- Supports single PDF or entire directory
- Extracts raw text + metadata (source file, page number)
- Output: list of `Document` objects

### 3.2 Chunking Strategy (`chunking.py`)
- Algorithm: `RecursiveCharacterTextSplitter`
- Chunk size: **500 characters** (balances context vs retrieval precision)
- Overlap: **50 characters** (preserves sentence context at boundaries)
- Split order: `paragraph → sentence → word → character`
- Overlap ensures sentences cut at boundaries aren't lost

### 3.3 Embedding Model (`embeddings.py`)
- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Dimension: 384-dimensional dense vectors
- Runs locally on CPU (no API key required)
- Normalised embeddings for cosine similarity

### 3.4 Vector Store (`vector_store.py`)
- Database: **ChromaDB** (local, persistent, no server)
- Stores chunk text + embedding + metadata
- Persisted to `data/chroma_db/` directory
- Retrieval: top-K cosine similarity search (K=4 default)

### 3.5 Retriever
- Type: Similarity search retriever
- Returns top 4 most semantically similar chunks
- Each result includes text + source metadata

### 3.6 LLM (`rag_pipeline.py`)
- Default: **Mistral 7B** via Ollama (local, free)
- Optional: **GPT-3.5-turbo** via OpenAI API
- Temperature = 0 for deterministic, factual answers
- Strict prompt: answer only from given context

### 3.7 LangGraph (`langgraph_workflow.py`)
- Manages workflow as a directed graph
- Nodes: input validation → RAG → conditional routing → output
- Conditional edges enable dynamic path selection (HITL vs direct output)
- Shared `RAGState` TypedDict flows through all nodes

### 3.8 Routing Logic
- After generation, evaluates:
  - Low confidence phrases in answer → escalate
  - Sensitive keywords (billing, fraud, refund) → escalate
  - Otherwise → send to output directly

### 3.9 HITL Module (`hitl.py`)
- Detects escalation triggers
- Simulates routing to human agent (production: webhook/ticket system)
- Returns human-crafted response + ticket ID
- Logs escalation event

---

## 4. Data Flow

```
PDF Document
    ↓ PyPDFLoader
Raw Text (pages)
    ↓ RecursiveCharacterTextSplitter
Chunks [500 chars, 50 overlap]
    ↓ HuggingFace Embeddings
Vectors [384-dim float arrays]
    ↓ ChromaDB.from_documents()
Persisted Vector Store
    ↓ (at query time)
User Query → Embedding → Cosine Similarity Search
    ↓
Top-4 Relevant Chunks
    ↓ RAG Prompt (context + question)
LLM (Mistral/GPT) → Answer Text
    ↓ Confidence Check
Route: [Confident → Output] or [Uncertain → HITL → Human → Output]
    ↓
Final Answer to User
```

---

## 5. Technology Justification

### Why ChromaDB?
- Runs entirely in-process — zero infrastructure needed
- Persists to disk automatically (no Redis/Postgres setup)
- Native LangChain integration
- Suitable for single-machine deployments and demos
- Production path: migrate to Pinecone/Weaviate when scale needed

### Why LangGraph?
- Explicit state machine — every decision is visible and debuggable
- Conditional edges model real decision trees (route based on confidence)
- HITL flows are natural — pause graph, inject human input, resume
- Unlike LangChain LCEL chains, LangGraph supports loops and branching

### LLM Choice
| Option | Pros | Cons |
|---|---|---|
| Mistral 7B (Ollama) | Free, local, private | Needs GPU for speed |
| GPT-3.5-turbo | Fast, accurate | Paid API, data leaves system |
| Llama 3 (Ollama) | Strong, open-source | Large download |

Default: **Mistral 7B via Ollama** — zero cost, fully local, reproducible.

---

## 6. Scalability Considerations

### Large Documents
- Chunking is memory-efficient — process page by page
- ChromaDB can handle millions of vectors
- For 1000+ page corpora: switch to Weaviate or Qdrant with HNSW indexing

### High Query Load
- ChromaDB in-process = low latency for single user
- For concurrent users: run ChromaDB as HTTP server (`chroma run`)
- Add Redis cache for repeated query answers
- Horizontal scale: multiple FastAPI workers behind load balancer

### Latency Optimization
- Local LLM (Ollama): ~2–5s per query on CPU, ~0.5s on GPU
- Cache embeddings of common queries
- Reduce K from 4 to 2 for faster retrieval with minimal accuracy loss
- Stream LLM output token-by-token for perceived speed improvement
