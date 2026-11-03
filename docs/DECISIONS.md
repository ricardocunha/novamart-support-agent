# Decisions

Settled during the design grilling session (2026-11-03). Scope lives in [`../SCOPE.md`](../SCOPE.md).

## Stack
| # | Decision | Choice |
|---|---|---|
| D1 | Agent framework | **Google ADK (Python)** — `LlmAgent` + function tools |
| D2 | Model access | **Gemini API key** (`GOOGLE_API_KEY`) by default; Vertex AI via `GOOGLE_GENAI_USE_VERTEXAI=true`. Agent model: `gemini-3.5-flash` (configurable). *Revised during build: `gemini-2.5-*` is no longer available to new API keys.* |
| D11 | Tooling | Python **3.14** (fallback 3.13 if ADK deps lack wheels — documented), **uv**, `ruff`, `pytest`, no Docker |
| D15 | Python version | `requires-python = ">=3.14"` (local 3.14.8) |

## Grounding
| # | Decision | Choice |
|---|---|---|
| D3 | Strategy | Lightweight RAG exposed as `search_policies(query)` tool — Gemini embeddings + numpy cosine; results carry `doc_id#section` |
| D5 | Documents | ~7 invented NovaMart Markdown docs with front-matter (`doc_id`, `owner`, `last_updated`, `version`) and deliberate edge cases: returns & refunds, exchanges, warranty/electronics, price match, loyalty, click-and-collect/shipping, damaged-goods/escalation SOP |
| D12 | Index | `gemini-embedding-001`, chunked on `##` sections, cached to `data/index.npz` (committed), rebuilt when doc hashes **or the embedding model/dimensions** change. Relevance floor **0.55** (measured: covered queries 0.65–0.79, uncovered 0.51–0.63; the model makes the final relevance call) |

## Tools (D8)
1. `search_policies(query)` — RAG over docs.
2. `get_order_status(order_id)` — mock API over `data/orders.json` (~10 orders: delivered, in-transit, delayed, cancelled, partially refunded, click-and-collect ready); typed not-found error.
3. `create_escalation_ticket(summary, category, order_id?, cited_docs[], urgency)` → `data/tickets.jsonl`, returns ticket id.
4. `log_knowledge_gap(question, reason)` → `data/gaps.jsonl`.

## Behaviour contract (D9)
- Every policy claim cites a `chunk_id` retrieved **in this conversation** (refined from "this turn" so follow-ups like "yes, open the ticket" can reuse earlier lookups). No citation → no claim.
- Nothing relevant retrieved → say "I don't know", **auto-log gap**, **offer** (not auto-create) a ticket.
- Policy requires **manager** approval → answer and say who approves (associate: call your manager; manager: you can approve). No ticket — the manager is in the store. *Refined during build.*
- Policy requires **Ops** / above-manager action → answer **and** offer ticket.
- Out-of-scope (HR, salary, chit-chat) → polite redirect, no gap log.

## User context (D13)
Mock employee persona in ADK session state: `store_id`, `role` ∈ {associate, manager}; selected via env / `--role`. Tailors approval answers; stamps tickets with store.

## Creative idea (D6)
**Close the loop:** escalation tickets pre-filled with order lookup + cited policy, and a **knowledge-gap log** ops uses to fix their docs. Argued-only (README "more time"): deterministic return-eligibility tool.

## Surface (D4)
`adk web` for demo (shows tool traces) + thin CLI `python -m novamart_agent.chat`. No custom UI.

## Evaluation (D10, D17)
- `evals/cases.yaml`, 25 cases: grounded answers, tool lookups, multi-step (order + policy), declines, injection/out-of-scope, ticket flow.
- Custom runner: deterministic checks (expected tools called, required doc_ids cited, key facts regex, decline expected) + LLM-as-judge. Runner enforces "offer, don't auto-create": no single-turn case may call `create_escalation_ticket`.
- Judge: stronger model (`gemini-3.1-pro-preview`; revised from `gemini-2.5-pro`, unavailable), temperature 0, rubric 1–5 for faithfulness & correctness, pass threshold; `--no-judge` for offline/cheap runs.
- Output: `evals/report.md` scorecard. Mention `adk eval` / Vertex Gen AI Evaluation Service as production options.

## Production note stance (D16)
Hybrid: **Gemini Enterprise** as employee surface (SSO, Drive/SharePoint/Confluence connectors, governance) + **custom ADK agent on Vertex AI Agent Engine**, registered into Gemini Enterprise for transactional actions. Data: Vertex AI Search datastores; order API behind Apigee with least-privilege SA. Security: SSO identity propagation, role→tool permissions, VPC-SC, DLP on logs, Model Armor, audit logs. Quality: eval set as CI gate, online sampled judge, thumbs feedback, weekly gap review with ops, KPIs (deflection, escalation rate, time-to-answer).

## Process
| # | Decision | Choice |
|---|---|---|
| D7 | Time budget | ~5h core + small refinement pass; cuts listed in README (no Agent Engine deploy, no auth, JSON files as storage) |
| D14 | Repo | `git init` locally; push to public GitHub `novamart-support-agent` **only on explicit go-ahead** |
| D18 | Commits | Small logical commits (scaffold → docs → tools → agent → evals → notes) with Co-Authored-By trailer |

## Layout
```
novamart_agent/      agent.py, prompts.py, tools/, chat.py
docs/policies/*.md
data/                orders.json, tickets.jsonl, gaps.jsonl, index.npz
evals/               cases.yaml, run_evals.py, report.md
scripts/build_index.py
tests/
README.md  PRODUCTION.md  SCOPE.md
```
