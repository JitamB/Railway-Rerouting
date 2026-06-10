"""Runtime pipeline orchestrator.

Consumes validated events from the buffer and walks: k-hop subgraph -> ST-GNN inference
(+ OOD fallback) -> cost-sensitive trigger -> capacity-aware re-route -> template-first alert
(+ async LLM) -> push / WS. Recompute is **event-scoped** (touched subgraphs only), not a
global tick (audit-02 §1.5). See docs/workflow.md Part A.
"""

from __future__ import annotations


def run() -> None:
    """Main consume loop; blocks, processing events as they arrive."""
    ...


def process_event(event: dict) -> None:
    """Handle a single validated disruption event end-to-end."""
    ...


if __name__ == "__main__":
    run()
