# Architecture decisions

Significant decisions are recorded as short ADRs in a lightweight
[MADR](https://adr.github.io/madr/) format: context, decision, consequences and the alternatives that
were considered. They were written during the 2026 rebuild, which replaced a prototype whose agents,
integrations and deployment did not work as documented.

| ADR | Decision | Status |
|---|---|---|
| [0001](0001-google-adk-multi-agent.md) | A Google ADK 2.x `Workflow` graph for planning, one tool-using agent for chat | Accepted |
| [0002](0002-pgvector-over-faiss.md) | pgvector in Postgres for guide retrieval instead of an in-process FAISS index | Accepted |
| [0003](0003-firebase-authentication.md) | Firebase Authentication instead of custom JWT login | Accepted |
| [0004](0004-cloud-run-free-tier.md) | Cloud Run and managed free tiers instead of a self-hosted server | Accepted |
| [0005](0005-open-map-data.md) | OpenStreetMap and other open data instead of keyed commercial APIs | Accepted |
| [0006](0006-simulated-bookings-human-in-the-loop.md) | Simulated bookings that only the user can confirm | Accepted |
| [0007](0007-ports-and-adapters.md) | Ports and adapters with deterministic fakes for every external service | Accepted |

## Template

```markdown
# NNNN. Title in the imperative

- Status: proposed | accepted | superseded by NNNN
- Date: YYYY-MM-DD

## Context
What forces the decision: requirements, constraints, problems with the current state.

## Decision
What we do, specifically enough to check against the code.

## Consequences
What gets better, what gets worse, what we must now take care of.

## Alternatives considered
Each option and why it lost.
```
