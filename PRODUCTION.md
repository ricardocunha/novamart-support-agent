# From prototype to production: NovaMart Assist on Google Cloud

## 1. Gemini Enterprise or a custom build? Both, split by job.
**Buy the platform, build the differentiating actions.**
- **Gemini Enterprise is the front door** for store and ops staff. It provides SSO, a governed chat UI on desktop and mobile, ready-made connectors (Drive, SharePoint, Confluence, ServiceNow), document-level permissions, and admin controls. Rebuilding any of that would be waste. On its own it answers "what does the returns policy say?"
- **This ADK agent is the custom piece.** It is deployed on **Vertex AI Agent Engine** and **registered in Gemini Enterprise** (via the agent gallery or A2A), so employees reach it from the same surface. It owns what a generic assistant can't do safely: live order lookups, NovaMart's approval rules (associate vs. manager), deterministic eligibility checks, and the escalation and knowledge-gap loop into Ops.
- **Lock-in check:** the agent is plain ADK and Gemini, with tools behind clean interfaces. It can run on Cloud Run or behind another channel (Chat, a POS handheld) without rewriting it.

## 2. Connecting real data
| Prototype | Production |
|---|---|
| Markdown files + numpy index | **Vertex AI Search** datastore (or a Gemini Enterprise data store) synced from the policy owner's source system (SharePoint/Drive/Confluence). Metadata is kept: `doc_id`, owner, version, effective date. `search_policies` keeps the same contract, so the agent doesn't change. |
| `orders.json` | Order management API exposed through **Apigee**: read-only scope, rate-limited, with PII fields masked (no full addresses or payment details). |
| `tickets.jsonl` | Ops ticketing system (ServiceNow/Jira) through its API or an Integration Connector. |
| `gaps.jsonl` | **BigQuery** table feeding a Looker dashboard for Ops and document owners. |

Policy freshness becomes a governed process. Document owners publish and the index re-syncs, so stale chunks never live in a vector DB nobody owns. Each answer cites `doc_id#section`, which makes it auditable against a document version.

## 3. Security & governance
- **Identity:** the employee's SSO identity (Google Workspace or Entra through Workforce Identity Federation) reaches the tools. `role` and `store_id` come from verified claims, not from the prompt. Tools enforce permissions server-side: the prompt *explains* the approval rules, but the API *enforces* them.
- **Least privilege:** one service account per tool. The agent can read orders but cannot refund. Write actions (tickets) need explicit user confirmation, which the prototype already requires.
- **Perimeter & data:** VPC Service Controls around Vertex AI, BigQuery and Apigee. Data stays in an EU or US region as required. Enterprise terms mean prompts aren't used for training.
- **Safety:** **Model Armor** screens for prompt injection and jailbreaks on input and tool output. **Cloud DLP** redacts PII before conversation logs are stored. Cloud Audit Logs record every tool call.
- **Change control:** prompt, model version and documents are versioned. Changes ship only through the eval gate below.

## 4. Evaluating & monitoring quality over time
- **Offline gate (CI):** the eval set in `evals/` grows from 25 cases to ~200, seeded with real questions from the gap log and from ops tickets. It runs deterministic checks (right tools, required citations, no fabricated citations, must and must-not phrases) plus an LLM judge for faithfulness and correctness. A model, prompt or document change can't ship if it regresses the pass rate. At scale this moves to the **Vertex AI Gen AI Evaluation Service**.
- **Online:** OpenTelemetry traces to Cloud Trace, recording every retrieval, tool call and latency. Each answer gets a thumbs up/down. A daily sample of conversations is scored by the same judge, and drift alerts fire in Cloud Monitoring.
- **Business KPIs** (what Ops actually cares about): **deflection rate** (questions resolved without an Ops contact), the **ticket rate**, and how complete tickets are (no call-backs needed), **time-to-answer at the counter**, and the trend in **knowledge gaps**.
- **The human loop:** a weekly 30-minute gap review with Ops. Top gaps are fixed in the documents, new cases join the eval set, and the docs, the agent and the evals improve together.

**Rollout:** pilot in 3 stores, with shadow mode and real Ops answers compared against the agent's. Then go regional with KPI targets agreed upfront, then chain-wide.
