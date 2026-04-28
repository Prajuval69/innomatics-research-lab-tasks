"""
langgraph_workflow.py
---------------------
LangGraph workflow for the demo-safe RAG customer support assistant.

Graph nodes:
  ┌─────────────┐
  │  INPUT NODE │  ← Validates user query
  └──────┬──────┘
         ↓
  ┌─────────────┐
  │ RETRIEVAL + │  ← FAISS retrieval + deterministic answer format
  │ FORMATTING  │    (no LLM, no API call)
  └──────┬──────┘
         ↓ (conditional routing)
        / \\
       /   \\
 [HITL]   [OUTPUT]
   ↓           ↓
 Human      Return
 Agent      Answer

✅ CHANGED: Removed get_llm import — no LLM used anymore
✅ CHANGED: _get_resources() no longer initialises _llm
✅ CHANGED: node_output prints sources list from state
❌ REMOVED: _llm global, get_llm() call
"""

from typing import Any, Dict, TypedDict
from langgraph.graph import StateGraph, END

# ✅ CHANGED: removed get_llm import — pipeline is API-free
from rag_pipeline import run_rag
from vector_store  import load_vector_store, get_retriever
from hitl          import should_escalate, simulate_human_response, log_escalation


# ── State Schema ───────────────────────────────────────
class RAGState(TypedDict):
    """Shared state object passed between all graph nodes."""
    query          : str
    answer         : str
    source_chunks  : list
    sources        : list   # ✅ ADDED: human-readable source strings
    low_confidence : bool
    escalated      : bool
    handled_by     : str
    ticket_id      : str
    error          : str
# ────────────────────────────────────────────────────────


# ── Initialise shared resources ────────────────────────
_store     = None
_retriever = None

def _get_resources():
    """
    Lazy-load FAISS vector store and retriever.
    ✅ CHANGED: No _llm — pipeline needs no LLM anymore.
    """
    global _store, _retriever
    if _store is None:
        _store     = load_vector_store()
        _retriever = get_retriever(_store)
    return _retriever
# ────────────────────────────────────────────────────────


# ═══════════════════════════════════════════════════════
# NODE FUNCTIONS
# ═══════════════════════════════════════════════════════

def node_input(state: RAGState) -> RAGState:
    """
    INPUT NODE
    Validates the incoming query.
    Strips whitespace, checks it's non-empty.
    """
    print(f"\n[Node: Input] Query received: '{state['query']}'")
    query = state.get("query", "").strip()

    if not query:
        return {
            **state,
            "answer"        : "Please enter a valid question.",
            "low_confidence": True,
            "error"         : "empty_query",
        }

    return {**state, "query": query, "error": ""}


def node_retrieval_and_generation(state: RAGState) -> RAGState:
    """
    RETRIEVAL + FORMATTING NODE
    ✅ CHANGED: No LLM call. Retrieves chunks via FAISS,
    formats answer deterministically. Always succeeds.
    """
    print("[Node: RAG] Running FAISS retrieval + answer formatting...")

    # ✅ CHANGED: Only retriever returned — no llm
    retriever = _get_resources()

    try:
        # llm=None is accepted by run_rag (ignored internally)
        result = run_rag(state["query"], retriever, llm=None)
        return {
            **state,
            "answer"        : result["answer"],
            "source_chunks" : result["source_chunks"],
            "sources"       : result.get("sources", []),
            "low_confidence": result["low_confidence"],
            "error"         : "",
        }
    except Exception as e:
        print(f"[Node: RAG] Unexpected error: {e}")
        return {
            **state,
            "answer"        : "Unable to process your query. Please try again.",
            "source_chunks" : [],
            "sources"       : [],
            "low_confidence": True,
            "error"         : str(e),
        }


def node_hitl(state: RAGState) -> RAGState:
    """
    HITL NODE
    Escalates to human agent when low-confidence answer detected.
    """
    print("[Node: HITL] Escalating to human agent...")
    updated_state = simulate_human_response(state)
    log_escalation(updated_state)
    return updated_state


def node_output(state: RAGState) -> RAGState:
    """
    OUTPUT NODE
    ✅ CHANGED: Prints sources list from state (not rebuilt here).
    Formats final response for CLI display.
    """
    print("[Node: Output] Preparing final response...")

    print(f"\n{'='*60}")
    print(f"  FINAL ANSWER")
    print(f"{'='*60}")
    print(f"  Q: {state['query']}")
    print(f"\n  A: {state['answer']}")

    # ✅ CHANGED: Use pre-built sources list from rag_pipeline
    sources = state.get("sources", [])
    if sources:
        print("  Sources:")
        for s in sources:
            print(f"    • {s}")

    print(f"  Handled by: {state.get('handled_by', 'ai_agent')}")
    print(f"{'='*60}\n")

    return state


# ═══════════════════════════════════════════════════════
# ROUTING LOGIC
# ═══════════════════════════════════════════════════════

def route_after_generation(state: RAGState) -> str:
    """
    Conditional edge after retrieval + formatting.
    → "hitl"   if answer is low-confidence or escalation needed
    → "output" if answer is ready
    """
    if state.get("error") == "empty_query":
        return "output"

    if should_escalate(state):
        return "hitl"

    return "output"


# ═══════════════════════════════════════════════════════
# BUILD GRAPH
# ═══════════════════════════════════════════════════════

def build_graph() -> StateGraph:
    """Assemble and compile the LangGraph workflow."""

    graph = StateGraph(RAGState)

    graph.add_node("input",  node_input)
    graph.add_node("rag",    node_retrieval_and_generation)
    graph.add_node("hitl",   node_hitl)
    graph.add_node("output", node_output)

    graph.set_entry_point("input")
    graph.add_edge("input", "rag")

    graph.add_conditional_edges(
        "rag",
        route_after_generation,
        {
            "hitl"  : "hitl",
            "output": "output",
        }
    )

    graph.add_edge("hitl",   "output")
    graph.add_edge("output", END)

    return graph.compile()


# ═══════════════════════════════════════════════════════
# MAIN RUNNER
# ═══════════════════════════════════════════════════════

def run_assistant(query: str) -> Dict[str, Any]:
    """Public entry point. Takes a query string, returns final state."""
    app = build_graph()

    initial_state: RAGState = {
        "query"         : query,
        "answer"        : "",
        "source_chunks" : [],
        "sources"       : [],
        "low_confidence": False,
        "escalated"     : False,
        "handled_by"    : "ai_agent",
        "ticket_id"     : "",
        "error"         : "",
    }

    final_state = app.invoke(initial_state)
    return final_state


if __name__ == "__main__":
    queries = [
        "What is ShopEase?",
        "What is the return policy?",
        "How do I track my order?",
    ]

    for q in queries:
        print(f"\n{'#'*60}")
        result = run_assistant(q)
        print(f"Escalated: {result.get('escalated', False)}")
