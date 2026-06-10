# `services/` — Backend Services

The serving and orchestration tier. Each subdirectory is an independently buildable service
(its own `pyproject.toml`; the two web-facing ones add a `Dockerfile`).

| Service | Role | Closes |
|---|---|---|
| [api/](api/) | FastAPI: REST + WebSocket + the open **Corridor Risk API** | — |
| [reroute-engine/](reroute-engine/) | **Capacity-aware re-routing — the core output** | audit-01 §5, audit-03 §3, audit-04 §7 |
| [llm-agent/](llm-agent/) | Claude phrasing — **template-first, async, non-blocking** | audit-02 §1.4/§3.5 |
| [notifier/](notifier/) | FCM push + **cost-sensitive** notification trigger | audit-02 §4 |
| [worker/](worker/) | Stream consumer that **orchestrates the runtime pipeline** + graceful degradation | audit-04 §1 |

**Orchestration:** the `worker` consumes the validated event stream and walks the pipeline
(subgraph → ST-GNN → trigger → re-route → alert); the `api` serves reads and the live
WebSocket feed. See [../docs/workflow.md](../docs/workflow.md) Part A, stages 5–9.
