"""
tests/test_queries.py
---------------------
Sample test queries to validate the RAG pipeline.
Run after building the vector store.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.langgraph_workflow import run_assistant


TEST_CASES = [
    # (query, expect_escalation)
    ("What is your return policy?",                 False),
    ("How long does standard shipping take?",        False),
    ("How do I track my order?",                    False),
    ("I want a refund for fraudulent charges",      True),
    ("I need to speak to a manager",                True),
    ("What is the capital of France?",              True),   # out of scope → low confidence
    ("",                                             False),  # empty query
]


def run_tests():
    print("\n" + "="*60)
    print("  RAG Assistant — Validation Test Suite")
    print("="*60)

    passed = 0
    failed = 0

    for query, expect_escalation in TEST_CASES:
        print(f"\nQ: '{query}'")
        result = run_assistant(query)

        got_escalation = result.get("escalated", False)
        status = "✅ PASS" if got_escalation == expect_escalation else "❌ FAIL"

        print(f"   Answer     : {result['answer'][:80]}...")
        print(f"   Escalated  : {got_escalation} (expected: {expect_escalation})")
        print(f"   Result     : {status}")

        if got_escalation == expect_escalation:
            passed += 1
        else:
            failed += 1

    print(f"\n{'='*60}")
    print(f"  Tests: {passed} passed, {failed} failed out of {len(TEST_CASES)}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    run_tests()
