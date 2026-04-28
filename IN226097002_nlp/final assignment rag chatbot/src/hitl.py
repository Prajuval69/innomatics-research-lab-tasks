"""
hitl.py
-------
Human-in-the-Loop (HITL) module.

Simulates escalation to a human agent when:
  - LLM confidence is low
  - Query is about sensitive topics (billing, legal)
  - User explicitly asks for a human

In production: replace simulate_human_response() with
  - Email/ticket system API
  - Live chat system webhook
  - Slack bot notification
"""

import time
from typing import Dict, Any


# ── Escalation trigger keywords ────────────────────────
SENSITIVE_TOPICS = [
    "refund", "lawsuit", "legal", "charge", "billing",
    "fraud", "hack", "complaint", "escalate", "human agent",
    "manager", "supervisor",
]
# ────────────────────────────────────────────────────────


def should_escalate(state: Dict[str, Any]) -> bool:
    """
    Decide if query needs human intervention.

    Triggers escalation if:
      1. LLM flagged low confidence, OR
      2. Query contains sensitive topic keywords
    """
    query = state.get("query", "").lower()

    if state.get("low_confidence", False):
        print("[HITL] Trigger: Low confidence answer detected.")
        return True

    for topic in SENSITIVE_TOPICS:
        if topic in query:
            print(f"[HITL] Trigger: Sensitive topic detected → '{topic}'")
            return True

    return False


def simulate_human_response(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate human agent reviewing and responding.

    In production:
      - Send to ticket system
      - Wait for webhook callback
      - Merge human answer back into conversation
    """
    print("\n" + "="*55)
    print("  🔔  ESCALATED TO HUMAN AGENT")
    print("="*55)
    print(f"  Customer Query : {state['query']}")
    print(f"  AI Draft Answer: {state.get('answer', 'N/A')[:100]}...")
    print("="*55)

    # ── Simulate human agent delay ─────────────────────
    print("\n  [Simulating] Human agent reviewing... (2s delay)")
    time.sleep(2)

    # ── Simulated human response ───────────────────────
    human_answer = (
        "Thank you for reaching out. A human support agent has reviewed "
        "your query. For this specific issue, please contact our dedicated "
        "support team at support@company.com or call 1-800-SUPPORT. "
        "We aim to resolve billing and sensitive matters within 24 hours."
    )

    print(f"\n  ✅ Human Agent Response:\n  {human_answer}\n")

    return {
        **state,
        "answer"       : human_answer,
        "escalated"    : True,
        "handled_by"   : "human_agent",
        "ticket_id"    : f"TKT-{int(time.time())}",   # simulated ticket ID
    }


def log_escalation(state: Dict[str, Any]) -> None:
    """Log escalation event (would write to DB/log file in production)."""
    print(f"[HITL] Escalation logged → Ticket: {state.get('ticket_id', 'N/A')}")


if __name__ == "__main__":
    # Test escalation with a billing query
    test_state = {
        "query"         : "I want a refund for my order",
        "answer"        : "I don't have enough information to answer this.",
        "low_confidence": True,
        "source_chunks" : [],
    }

    if should_escalate(test_state):
        final_state = simulate_human_response(test_state)
        log_escalation(final_state)
        print(f"\nFinal state keys: {list(final_state.keys())}")
