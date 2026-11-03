# SCOPE — Take-Home Case Study

> Source of truth for this project. Every design and implementation decision should trace back to this brief.
> Decisions made on top of it live in `docs/DECISIONS.md` (to be created after the grilling session).

**Role:** Senior Deployed AI Engineer – Gemini Enterprise (Artefact)

## About This Case

Thank you for your interest in Artefact. This case study is the first step of our technical process: your submission will be the basis of Interview 1, where you will present your solution and discuss your choices with our engineers.

- **Time:** the case is designed for 4–6 focused hours. Please do not over-invest — we value clear thinking over polish.
- **AI tools:** the use of AI assistants (Gemini CLI, Claude Code, Cursor, etc.) is allowed and encouraged — we work this way too. You must, however, understand and be able to defend every decision and every line of code you submit.

## The Scenario

NovaMart, a mid-size retailer, is overwhelmed with internal support requests. Store employees constantly ask the operations team about product policies, returns, and order issues. NovaMart wants an internal AI assistant that answers these questions reliably, grounded in company documentation, and can look up live information when needed. They run on Google Cloud and are evaluating Gemini Enterprise.

## Your Task

### 1. Build a working prototype

Using the Google AI stack (Gemini models via the Gemini API; Vertex AI and the Agent Development Kit are welcome but not required), build a small agent that can:

- Answer questions grounded in a small document set you assemble yourself (5–10 short policy or product documents — public or invented — is enough).
- Call at least one tool — for example, a mock order-status API you stub out.
- Decline gracefully when it does not know the answer, instead of inventing one.

Any interaction surface is fine: CLI, notebook, or a simple UI. Include a basic evaluation: a handful of test questions and how you check the quality of the answers.

### 2. Write a short production note (1 page max)

Describe how you would take this prototype to production for NovaMart on Google's enterprise stack. Cover, briefly:

- whether and how you would use Gemini Enterprise versus a custom build,
- how you would connect the client's real data,
- how you would handle security and governance,
- how you would evaluate and monitor quality over time.

### 3. Be creative

The brief above is simple on purpose: it leaves room for you. Put yourself in the shoes of NovaMart's business users — the store employees and the operations team — and go beyond the brief where you see value: a feature they would ask for, a smarter interaction, a better way to close the loop on their problem.

Creativity does not mean more features: one well-chosen idea, built or simply argued in your README, is worth more than five half-finished ones. We want to see your ability to turn a business problem into a solution users would actually want.

## What to Submit

- A Git repository (public link or invite) with a README covering setup instructions, your key decisions, and what you would do with more time.
- Your production note, as a Markdown or PDF file in the repository.
- Submit the repository link through the Greenhouse application portal.

## How We Evaluate

We look for end-to-end thinking, working software over polish, sound use of the Google AI stack, an evaluation mindset, creativity in solving the business problem, and clear communication in your README and production note. We are **not** evaluating UI design, document volume, or feature count. If something is ambiguous, make a reasonable assumption and state it — that is part of the job.

## Deliverables checklist

- [ ] Agent prototype (Gemini) — grounded answers over 5–10 docs
- [ ] ≥1 tool call (e.g. mock order-status API)
- [ ] Graceful decline when unknown
- [ ] Interaction surface (CLI / notebook / simple UI)
- [ ] Evaluation: test questions + how quality is checked
- [ ] `PRODUCTION.md` — 1 page max (Gemini Enterprise vs custom, data connection, security/governance, eval & monitoring)
- [ ] One well-chosen creative idea (built or argued)
- [ ] README: setup, key decisions, what with more time
- [ ] Stated assumptions
- [ ] Public Git repo, link submitted via Greenhouse
