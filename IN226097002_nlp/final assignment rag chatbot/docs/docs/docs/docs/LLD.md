# LOW-LEVEL DESIGN (LLD)
## RAG-Based Customer Support Assistant with LangGraph & HITL
**Project:** Innomatics Research Labs — Mandatory Internship Project
**Version:** 1.0

---

## 1. Module-Level Design

### 1.1 Document Processing Module (`ingestion.py`)

```
Function: load_pdf(file_path: str) → List[Document]
  Input : absolute or relative path to .pdf
  Output: list of LangChain Document objects (one per page)
  Error : FileNotFoundError if path invalid

Function: load_directory(dir_path: str) → List[Document]
  Input : directory path containing PDF files
  Output: all pages from all PDFs as Document list
  Uses  : DirectoryLoader with glob="**/*.pdf"

Function: load_documents(path: str) → List[Document]
  Input : file path OR directory path
  Output: calls appropriate loader automatically
  Logic : Path(path).is_file() → load_pdf
          Path(path).is_dir()  → load_directory
```

### 1.2 Chunking Module (`chunking.py`)

```
Function: chunk_documents(documents: List[Document]) → List[Document]
  Input : raw Document objects from ingestion
  Output: smaller Document objects (chunks)
  Config:
    chunk_size    = 500 chars
    chunk_overlap = 50 chars
    separators    = ["\n\n", "\n", ". ", " ", ""]
  Logic : RecursiveCharacterTextSplitter tries each separator
          in order, splits only when chunk would exceed size

Function: preview_chunks(chunks, n=3) → None
  Debug utility: prints first n chunks with metadata
```

### 1.3 Embedding Module (`embeddings.py`)

```
Function: get_embedding_model() → HuggingFaceEmbeddings
  Model   : sentence-transformers/all-MiniLM-L6-v2
  Device  : cpu (configurable to cuda)
  Output  : 384-dimensional normalised float vectors
  Caching : model downloaded once to ~/.cache/huggingface/
```

### 1.4 Vector Storage Module (`vector_store.py`)

```
Function: build_vector_store(chunks) → Chroma
  Input : List[Document] chunks
  Action: embed all chunks, store in ChromaDB
  Persist: data/chroma_db/

Function: load_vector_store() → Optional[Chroma]
  Action: load existing store from disk
  Returns None if store not yet built

Function: get_retriever(vector_store, k=4) → Retriever
  Type: similarity search
  k   : number of chunks to return per query
```

### 1.5 Retrieval Module (inside `rag_pipeline.py`)

```
Function: run_rag(query, retriever, llm) → Dict
  Step 1: retriever.get_relevant_documents(query)
          → returns top-k Document objects
  Step 2: build context string from chunk text + metadata
  Step 3: format RAG_PROMPT with context + question
  Step 4: llm.invoke(prompt) → answer string
  Step 5: is_low_confidence(answer) → bool
```

### 1.6 Query Processing Module (`rag_pipeline.py`)

```
Function: is_low_confidence(answer: str) → bool
  Checks if answer contains any LOW_CONFIDENCE_PHRASES:
    ["i don't have enough information",
     "i cannot answer",
     "not in the context",
     "i'm not sure",
     "unable to find"]

Function: get_llm(use_openai: bool) → LLM
  use_openai=False: Ollama(model="mistral", temperature=0)
  use_openai=True : ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
```

### 1.7 LangGraph Execution Module (`langgraph_workflow.py`)

```
Graph nodes   : input, rag, hitl, output
Entry point   : "input"
Conditional   : route_after_generation() after "rag" node
Terminal      : END after "output" node

Function: build_graph() → CompiledGraph
  Creates StateGraph(RAGState)
  Adds all nodes and edges
  Compiles and returns runnable graph

Function: run_assistant(query: str) → Dict
  Public API: builds graph, runs with initial state
```

### 1.8 HITL Module (`hitl.py`)

```
Function: should_escalate(state) → bool
  Condition 1: state["low_confidence"] == True
  Condition 2: any SENSITIVE_TOPICS keyword in query.lower()
  Returns True if either condition met

Function: simulate_human_response(state) → Dict
  Prints escalation notice
  Adds simulated 2-second delay
  Returns updated state with human answer + ticket_id

Function: log_escalation(state) → None
  Logs ticket ID (production: writes to DB/log file)
```

---

## 2. Data Structures

### 2.1 Document Format (LangChain)
```python
Document(
    page_content = "Raw text extracted from PDF page...",
    metadata     = {
        "source": "data/sample_docs/policy.pdf",
        "page"  : 3
    }
)
```

### 2.2 Chunk Structure
```python
Document(
    page_content = "...500-char excerpt from document...",
    metadata     = {
        "source"   : "policy.pdf",
        "page"     : 3,
        "chunk_id" : "auto-assigned by splitter"
    }
)
```

### 2.3 Embedding Representation
```python
{
    "id"       : "uuid-auto-generated",
    "text"     : "chunk text content",
    "embedding": [0.021, -0.134, 0.089, ...],  # 384 floats
    "metadata" : {"source": "...", "page": N}
}
```

### 2.4 Query-Response Schema
```python
{
    "query"         : str,    # original user question
    "answer"        : str,    # LLM or human agent answer
    "source_chunks" : list,   # list of Document objects used
    "low_confidence": bool,   # True if answer seems uncertain
    "escalated"     : bool,   # True if routed to human
    "handled_by"    : str,    # "ai_agent" or "human_agent"
    "ticket_id"     : str,    # escalation ticket (if applicable)
    "error"         : str     # error message if any, else ""
}
```

### 2.5 LangGraph State Object
```python
class RAGState(TypedDict):
    query          : str
    answer         : str
    source_chunks  : list
    low_confidence : bool
    escalated      : bool
    handled_by     : str
    ticket_id      : str
    error          : str
```
All fields must be present in initial state. Nodes merge updates via `{**state, "key": new_value}`.

---

## 3. LangGraph Workflow Design

### 3.1 Nodes

| Node | Function | Input Fields Used | Output Fields Modified |
|------|----------|------------------|----------------------|
| `input` | Validate query | `query` | `query`, `error` |
| `rag` | Retrieve + Generate | `query` | `answer`, `source_chunks`, `low_confidence`, `error` |
| `hitl` | Human escalation | `query`, `answer` | `answer`, `escalated`, `handled_by`, `ticket_id` |
| `output` | Format + display | all fields | (read-only, terminal) |

### 3.2 Edges

```
START → input
input → rag         [unconditional]
rag   → hitl        [if should_escalate(state) == True]
rag   → output      [if should_escalate(state) == False]
hitl  → output      [unconditional]
output → END        [unconditional]
```

### 3.3 State Transitions

```
Initial State:
  query="How to return?", answer="", low_confidence=False, escalated=False

After node_input:
  query="How to return?"   ← cleaned/validated

After node_rag:
  answer="You can return..."  ← LLM generated
  source_chunks=[...]         ← retrieved docs
  low_confidence=False        ← answer is confident

route_after_generation → "output"   ← no escalation needed

After node_output:
  [final state displayed, graph ends]
```

---

## 4. Conditional Routing Logic

```python
def route_after_generation(state: RAGState) -> str:
    # Priority 1: empty query error
    if state.get("error") == "empty_query":
        return "output"

    # Priority 2: escalate if HITL triggered
    if should_escalate(state):
        return "hitl"

    # Default: go directly to output
    return "output"
```

### Escalation Triggers
| Trigger | Detection Method |
|---|---|
| Low confidence answer | `is_low_confidence(answer)` = True |
| Sensitive keywords | query contains: refund, fraud, billing, legal, lawsuit, etc. |
| Empty/invalid query | `error == "empty_query"` |

### Complex Query Handling
- LLM cannot answer → low_confidence=True → HITL
- Multiple topics in one query → LLM attempts best-effort answer
- Query longer than 512 tokens → LangChain truncates to model limit

---

## 5. HITL Design

### 5.1 When Escalation is Triggered
- `low_confidence = True` in RAG output
- Query contains SENSITIVE_TOPICS keywords

### 5.2 What Happens After Escalation
1. `node_hitl` called with current state
2. `simulate_human_response()` runs → prints escalation notice
3. Human response injected into state as `answer`
4. `ticket_id` generated (format: `TKT-{unix_timestamp}`)
5. `escalated=True`, `handled_by="human_agent"` set
6. Flow continues to `node_output`

### 5.3 How Human Response is Integrated
```python
updated_state = {
    **state,                         # preserve all original fields
    "answer"    : human_answer,      # override AI answer with human answer
    "escalated" : True,
    "handled_by": "human_agent",
    "ticket_id" : f"TKT-{int(time.time())}",
}
```

**Production integration pattern:**
```python
# Replace simulate_human_response() with:
ticket = create_zendesk_ticket(query=state["query"], ai_draft=state["answer"])
human_response = wait_for_ticket_resolution(ticket.id, timeout=3600)
return {**state, "answer": human_response, "ticket_id": ticket.id}
```

---

## 6. API / Interface Design

### 6.1 Input Format
```python
# CLI
query: str   # plain text user question

# Programmatic
result = run_assistant("What is your return policy?")
```

### 6.2 Output Format
```python
{
    "query"         : "What is your return policy?",
    "answer"        : "Our return policy allows...",
    "source_chunks" : [Document(...), Document(...)],
    "low_confidence": False,
    "escalated"     : False,
    "handled_by"    : "ai_agent",
    "ticket_id"     : "",
    "error"         : ""
}
```

---

## 7. Error Handling

| Error Scenario | Detection | Response |
|---|---|---|
| No relevant chunks found | `chunks == []` | Return "No relevant information found" |
| LLM API failure | `try/except` around `llm.invoke()` | Return "System error. Please try again." + set `error` |
| PDF file not found | `FileNotFoundError` in loader | Raise with descriptive message |
| ChromaDB not built | `os.path.exists()` check | Prompt user to run ingestion first |
| Empty user query | `query.strip() == ""` | Return "Please provide a valid question." |
| LLM returns empty string | `answer.strip() == ""` | Treat as low_confidence=True |
