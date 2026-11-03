# From prototype to production: NovaMart Assist on Google Cloud

## 1. Gemini Enterprise or a custom build? Both, split by job
**Buy the platform, build the differentiating actions.**
- **Gemini Enterprise is the front door.** It brings SSO, a governed chat UI, ready-made connectors (Drive, SharePoint, Confluence, ServiceNow), document-level permissions and admin controls. Rebuilding any of that would be waste. On its own it can answer "what does the returns policy say?".
- **This ADK agent is the custom part.** It is deployed on **Vertex AI Agent Engine** and **registered in Gemini Enterprise**, so staff reach it from the same place. It owns what a generic assistant can't do safely: live order lookups, NovaMart's role-based approval rules, and the escalation and knowledge-gap loop into Ops.
- **No lock-in:** it is plain ADK with tools behind clean interfaces, so it can also run on Cloud Run or behind another channel, such as Google Chat or the POS handheld.

## 2. Connecting real data
- **Policies:** move from Markdown files to a **Vertex AI Search** (or Gemini Enterprise) data store, synced from wherever the document owners publish, with `doc_id`, owner, version and effective date kept as metadata. `search_policies` keeps its contract, so the agent itself doesn't change. Document owners stay in charge of what is current, and every cited `doc_id#section` can be traced to a version.
- **Orders:** the order management API, exposed through **Apigee**. Read-only, rate-limited, with PII fields masked.
- **Tickets → ServiceNow/Jira; knowledge gaps → BigQuery**, with a Looker view for Ops and document owners.

## 3. Security & governance
- **Identity:** `role` and `store_id` come from verified SSO claims (Workspace, or Entra through Workforce Identity Federation), never from the prompt. Tools enforce permissions server-side: the prompt *explains* approval limits, and the API *enforces* them.
- **Least privilege:** one service account per tool. The agent can read orders but can't issue refunds, and any write (a ticket) needs the user's explicit confirmation, as it already does in the prototype.
- **Perimeter & data:** VPC Service Controls around Vertex AI, BigQuery and Apigee. Data residency is set per region. Enterprise terms rule out training on prompts.
- **Safety:** **Model Armor** screens inputs and tool outputs for prompt injection. **Cloud DLP** redacts PII before logs are stored. Cloud Audit Logs record every tool call.
- **Change control:** prompt, model and document versions are tracked, and nothing ships without passing the eval gate.

## 4. Evaluating & monitoring quality over time
- **Offline gate in CI:** grow `evals/` from 25 cases to about 200, adding a **held-out** set drawn from real gap-log questions and Ops tickets. Run several trials per case and gate on the pass rate (deterministic checks plus a judge for faithfulness and correctness). At scale, move to `adk eval` and the **Vertex AI Gen AI Evaluation Service**.
- **Online:** OpenTelemetry traces in Cloud Trace (retrievals, tool calls, latency), thumbs up/down feedback, a daily sample scored by the judge, and drift alerts in Cloud Monitoring.
- **KPIs Ops cares about:** deflection rate (questions answered without contacting Ops), ticket rate and ticket completeness (no call-backs needed), time to answer at the counter, and the knowledge-gap trend.
- **Human loop:** a weekly 30-minute gap review with Ops. The top gaps get fixed in the documents and become new eval cases.

**Rollout:** a 3-store pilot in shadow mode, comparing the agent's answers with what Ops actually said, then regional, then chain-wide. KPI targets are agreed before the pilot starts.
