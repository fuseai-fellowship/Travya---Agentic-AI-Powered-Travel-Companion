# 0001. Use Google ADK workflow agents for trip planning

- Status: accepted
- Date: 2026-11-04

## Context

Travya's purpose is to show agents doing real work, so the planning flow has to be a genuine
multi-agent system, not one prompt with a label on it. The prototype described an ADK multi-agent
system, but its live path did not use ADK: orchestration was hand-written, research returned an
apology string because of an async bug, and a "booker" agent booked a mock flight on every run.

Requirements for the rebuild:

- research from several sources at once, without spending model tokens on plain data fetching;
- a draft, a review and a bounded number of revisions;
- structured, validated output that can be stored and mapped;
- every step visible to the user as it happens;
- a deterministic path for tests and keyless demos;
- conversation memory for the assistant.

## Decision

Use [Google ADK](https://google.github.io/adk-docs/) workflow agents with Gemini
(`backend/app/agents/planning/pipeline.py`):

- `SequentialAgent "trip_planner"` runs `ParallelAgent "research"`, then `LlmAgent "planner"`, then
  `LoopAgent "refine"` with at most two rounds of `critic`, `quality_gate` and `reviser`.
- The four research scouts are custom `BaseAgent`s that call the integration ports and write to
  session state; they use no model.
- The planner, critic and reviser use `output_schema` (`TripPlan`, `Critique`) and
  `include_contents="none"`, reading only what the state gives them.
- `QualityGate` is a custom `BaseAgent` that merges the critic's verdict with deterministic checks and
  ends the loop by escalating.
- Planning sessions are one-shot and use `InMemorySessionService`. The chat assistant is a single
  `LlmAgent` with five read-only tools, and its sessions persist in `DatabaseSessionService` in a
  separate `adk` schema.
- ADK runner events are translated into `AgentEvent`s and streamed over SSE.
- Without a key, `ScriptedPlanner` replaces the LLM part of the tree.

## Consequences

- Each agent has a name and emits events, so the UI's per-agent timeline comes straight from the
  runner; there is no separate progress-reporting code.
- Parallel fan-out and loop exit are framework semantics (`ParallelAgent`, `escalate`), not custom
  concurrency code.
- Research is cheap and testable: scouts are plain async functions behind an agent interface.
- The offline planner plugs into the same tree, so CI exercises the real pipeline structure, events
  and persistence.
- ADK is young and changes quickly; the version is pinned in `uv.lock` and updated through Dependabot
  with the test suite as the guard.
- Session state is an untyped dictionary. Validation happens at the edges: `TripPlan` on the way out,
  typed adapter models on the way in.
- ADK owns tables outside Alembic (the `adk` schema), which must be considered in backups and resets.
- After the second round the reviser's plan is stored without another critique; the schema check
  still applies and the final review is stored with the plan.

## Alternatives considered

- **LangGraph**: an explicit state graph with fine-grained control, but more code for the same
  sequential, parallel and loop shape, and no Gemini-native structured output path out of the box.
- **CrewAI**: role-based agents read well in a demo, but control over structured output and over
  deterministic, tokenless steps is weaker.
- **Plain asyncio and google-genai**: the fewest dependencies, but it would re-implement the event
  stream, sessions, tool calling and loop control.
- **One large prompt**: the cheapest option, with no parallel research, no independent review and
  nothing to show the user while it runs.
