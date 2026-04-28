# TECHNICAL DOCUMENTATION
## RAG-Based Customer Support Assistant with LangGraph & HITL
**Project:** Innomatics Research Labs — Mandatory Internship Project
**Version:** 1.0

---

## 1. Introduction

### What is RAG?
Retrieval-Augmented Generation (RAG) is a pattern that combines:
1. **Retrieval** — find relevant documents from a knowledge base
2. **Augmentation** — inject retrieved documents into an LLM prompt
3. **Generation** — LLM generates answer grounded in retrieved content

Without RAG, LLMs answer from training data, which may be outdated or absent for company-specific knowledge. With RAG, the LLM strictly uses provided context — no hallucination about policies it was never trained on.

### Why RAG is Needed
| Problem Without RAG | RAG Solution |
|---|---|
| LLM makes up answers | Answers grounded in real documents |
| Knowledge gets stale | Update ChromaDB without retraining LLM |
| LLM doesn't know your policies | Inject policy PDFs into knowledge base |
| Hallucination risk | "I don't know" if no relevant chunk found |

### Use Case
A customer support assistant for an e-commerce or SaaS company where:
- Support knowledge base exists as PDF documents
- Queries cover: return policy, shipping, billing, account issues
- Sensitive cases (refunds, fraud) need human agent review
- System must never invent policies that don't exist

---

## 2. System Architecture Explanation

The system has two phases:

**Phase 1: Offline Ingestion (run once)**
PDFs → PyPDFLoader extracts text per page → RecursiveCharacterTextSplitter cuts into 500-char chunks → HuggingFace `all-MiniLM-L6-v2` converts chunks to 384-dim vectors → ChromaDB stores vectors + metadata to disk.

**Phase 2: Online Query (per user query)**
User types question → LangGraph `input` node validates → `rag` node retrieves top-4 similar chunks from ChromaDB via cosine similarity → builds prompt with context → LLM generates answer → `route_after_generation` decides: confident answer goes to `output`; uncertain answer goes to `hitl` node for human escalation → final answer returned to user.

---

## 3. Design Decisions

### Chunk Size: 500 Characters
- Too small (100–200 chars): loses sentence context, retrieval fails
- Too large (1000+ chars): more noise in retrieved chunk, LLM gets confused
- 500 chars ≈ 3–5 sentences — ideal semantic unit for customer support queries

### Overlap: 50 Characters
- Boundary sentences split between chunks would lose context
- 50-char overlap ensures no sentence is cut off entirely
- Low enough that same content isn't retrieved twice redundantly

### Embedding Strategy
- `all-MiniLM-L6-v2` chosen for speed + quality tradeoff
- 384 dimensions: fast similarity search, low storage
- Normalised: cosine similarity = dot product (faster computation)
- Runs locally: no API cost, no data privacy risk

### Retrieval Method: Similarity Search (K=4)
- K=4 chunks gives enough context without overwhelming the LLM prompt
- Similarity search is exact and deterministic (vs MMR which is probabilistic)
- Production improvement: hybrid search (BM25 keyword + dense vector)

### Prompt Design
```
You are a helpful customer support assistant.
Use ONLY the context below to answer the question.
If the answer is not in the context, say: "I don't have enough information..."

Context: {retrieved chunks with source labels}
Question: {user query}
Answer:
```
Key design choices:
- "ONLY the context" → prevents hallucination
- Source labels in context → enables citation
- Explicit fallback phrase → triggers HITL when answer isn't in docs

---

## 4. Workflow Explanation

### LangGraph Usage
LangGraph models the assistant as a **directed state graph**. Each processing step is a **node**. The flow between steps is an **edge**. Conditional edges route to different nodes based on state.

This is superior to a simple function chain because:
- State is explicit and inspectable at every step
- Conditional branching (HITL vs direct output) is clean
- Future loops (user correction, retry) are easy to add

### Node Responsibilities

| Node | Responsibility | Reads | Writes |
|------|---------------|-------|--------|
| `node_input` | Validate/clean query | `query` | `query`, `error` |
| `node_retrieval_and_generation` | Full RAG pipeline | `query` | `answer`, `source_chunks`, `low_confidence` |
| `node_hitl` | Escalate to human | `query`, `answer` | `answer`, `escalated`, `ticket_id` |
| `node_output` | Display result | all | (terminal) |

### State Transitions
```
{query: "...", answer: "", low_confidence: False, escalated: False}
        ↓ node_input
{query: "cleaned query", error: ""}
        ↓ node_rag
{answer: "LLM answer", source_chunks: [...], low_confidence: True/False}
        ↓ route_after_generation (conditional)
     ↙           ↘
  hitl           output
{answer: "human answer",
 escalated: True,
 ticket_id: "TKT-..."}
     ↓
  output → END
```

---

## 5. Conditional Logic

### Intent Detection
Simple keyword-based detection (production: fine-tuned classifier):
- Sensitive topics list: `["refund", "fraud", "billing", "legal", ...]`
- Low confidence detection: string matching on LLM output phrases
- Advantage: transparent, debuggable, no model dependency
- Limitation: misses paraphrased sensitive queries ("get my money back" vs "refund")

### Routing Decisions
```
route_after_generation(state) → str:
    if error == "empty_query"      → "output"   (short-circuit)
    if low_confidence == True      → "hitl"     (AI uncertain)
    if sensitive keyword in query  → "hitl"     (policy escalation)
    else                           → "output"   (confident AI answer)
```

---

## 6. HITL Implementation

### Role of Human Intervention
Human agents handle:
- Queries where AI has no relevant information
- Sensitive financial/legal queries requiring human accountability
- Queries requiring access to live systems (CRM, order database)
- Complex multi-part questions beyond FAQ scope

### Current Implementation (Simulation)
```
detect escalation trigger
    ↓
print escalation notice with query + AI draft
    ↓
2-second simulated delay
    ↓
inject pre-written human response
    ↓
generate ticket ID (TKT-{timestamp})
    ↓
log escalation event
    ↓
return to LangGraph output node
```

### Benefits
- AI handles high-volume repetitive queries (80% of tickets)
- Human effort focused on complex, high-value cases
- AI draft answer helps human agent understand context quickly
- Audit trail via ticket IDs

### Limitations
- Simulation doesn't integrate with real ticketing systems (Zendesk, Freshdesk)
- No feedback loop — human corrections don't improve AI over time
- Keyword-based escalation misses paraphrased sensitive queries
- No SLA tracking on human response time

---

## 7. Challenges & Trade-offs

### Accuracy vs Speed
| Choice | Accuracy | Speed |
|---|---|---|
| GPT-4 | Very High | Slow (API latency) |
| GPT-3.5-turbo | High | Medium |
| Mistral 7B (GPU) | Good | Fast |
| Mistral 7B (CPU) | Good | Slow (2-5s) |

Current default: Mistral 7B on CPU — acceptable for demo, needs GPU for production.

### Cost vs Performance
| Component | Free Option | Paid Option |
|---|---|---|
| LLM | Ollama (local) | OpenAI API |
| Embeddings | HuggingFace (local) | OpenAI Ada-002 |
| Vector DB | ChromaDB (local) | Pinecone cloud |
| Hosting | None/local | AWS/GCP |

### Chunk Size Trade-off
- Smaller chunks → precise retrieval, lost context
- Larger chunks → more context, noisier retrieval, higher LLM cost

### K Retrieval Trade-off
- Lower K (1-2) → faster, less noise, may miss info
- Higher K (6-8) → more complete, prompt gets long, higher LLM cost

---

## 8. Testing Strategy

### Sample Queries
```
Category: FAQ (should answer confidently)
  Q: "What is your return policy?"
  Q: "How long does shipping take?"
  Q: "How do I track my order?"

Category: Out-of-scope (should trigger low confidence)
  Q: "What is the weather today?"
  Q: "Tell me about the history of Rome."

Category: Sensitive (should trigger HITL)
  Q: "I want a refund for fraudulent charges."
  Q: "I'm going to take legal action."
  Q: "I was charged twice for the same order."

Category: Edge cases
  Q: "" (empty)
  Q: "asdfghjkl" (nonsense)
  Q: "Can you help me?" (too vague)
```

### Validation Approach
1. **Grounding check:** Is the answer derivable from the retrieved chunks?
2. **Escalation check:** Does sensitive query correctly trigger HITL?
3. **Fallback check:** Does out-of-scope query produce low_confidence=True?
4. **Source check:** Are source citations accurate (page + file)?
5. **No hallucination:** Does AI ever state facts not in any chunk?

---

## 9. Future Enhancements

### Multi-Document Support
- Web scraper to ingest help center articles (not just PDFs)
- Support for DOCX, TXT, HTML document formats
- Auto re-ingestion when documents update (file watcher)

### Feedback Learning (RLHF-lite)
- Store each query-answer pair with user thumbs up/down
- Periodically fine-tune retrieval weights based on feedback
- Use positive examples to curate few-shot examples in prompt

### Memory Integration
- Conversation memory: remember what user said earlier in session
- User-level memory: remember preferences/history across sessions
- Use `ConversationBufferMemory` or `LangGraph` checkpointing

### Deployment
- Wrap `run_assistant()` in FastAPI endpoint
- Docker container with Ollama + ChromaDB pre-loaded
- Streamlit UI for non-CLI users
- Add authentication/rate limiting for production

### Improved HITL
- Integrate Zendesk/Freshdesk API for real ticket creation
- Webhook listener to receive human agent responses
- Real-time SLA dashboard showing escalation queue
- Feedback loop to automatically add resolved tickets to knowledge base
