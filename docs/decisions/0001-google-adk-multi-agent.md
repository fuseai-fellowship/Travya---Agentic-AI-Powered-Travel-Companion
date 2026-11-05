# 0001. Use a Google ADK Workflow graph for trip planning

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
- fast enough on free tiers that a user watches it finish;
- a deterministic path for tests and keyless demos;
- conversation memory for the assistant.

## Decision

Use [Google ADK](https://google.github.io/adk-docs/) 2.x with Gemini, and express planning as a
`Workflow` graph (`backend/app/agents/planning/pipeline.py`):

- `START` fans out to four research scouts that run concurrently; a `JoinNode` (`research_done`)
  waits for all of them; then `planner` → `critic` → `quality_gate`.
- `quality_gate` routes with `EventActions(route=...)`: `approved` goes to `finalize`, `revise` goes to
  `reviser`, whose output returns to `critic`. After two revisions the gate accepts the plan and keeps
  the remaining issues as notes.
- The scouts and the gate are custom `BaseAgent`s; the scouts call the integration ports, use no model
  and have a 30 s budget each.
- The planner, critic and reviser are `LlmAgent`s with `output_schema` (`TripPlan`, `Critique`) and
  `include_contents="none"`, reading only what the state gives them. The planner and reviser use Gemini
  Flash with an immediate Flash-Lite fallback; the critic uses Flash-Lite.
- Planning sessions are one-shot and use `InMemorySessionService`. The chat assistant is a single
  `LlmAgent` with five read-only tools, and its sessions persist in `DatabaseSessionService` in a
  separate `adk` schema.
- Runner events are translated into `AgentEvent`s and streamed over SSE.
- Without a key, the graph ends in `ScriptedPlanner` instead of the model nodes.

The container agents used by earlier ADK versions (`SequentialAgent`, `ParallelAgent`, `LoopAgent`)
are deprecated in ADK 2.x and are not used.

## Consequences

- Each node has a name and emits events, so the UI's per-agent timeline comes straight from the
  runner; there is no separate progress-reporting code.
- The shape of the flow is data: fan-out, join and conditional routes are declared as edges, and the
  revise path is an explicit edge rather than a loop with an escape flag.
- Every revision is critiqued and checked again before the plan is accepted.
- Research is cheap and testable: scouts are plain async functions behind an agent interface, and a
  slow source cannot hold the plan for longer than its budget. A live run took about 35 s in testing.
- The offline planner plugs into the same graph, so CI exercises the real structure, events and
  persistence.
- ADK is young and changes quickly (the 2.x move to workflow graphs is one example); the version is
  pinned in `uv.lock` and upgraded deliberately (`uv lock --upgrade`) with the test suite as the guard.
- Session state is an untyped dictionary. Validation happens at the edges: `TripPlan` on the way out,
  typed adapter models on the way in.
- ADK owns tables outside the application's models (the `adk` schema), which must be considered in
  backups and resets.

## Alternatives considered

- **ADK container agents** (`SequentialAgent`, `ParallelAgent`, `LoopAgent`): the first version of
  the rebuild used them; they are deprecated in ADK 2.x, and a loop with an escalation flag expresses
  "revise at most twice" less directly than a routed edge.
- **LangGraph**: an explicit state graph with fine-grained control, but a second framework next to
  Gemini's own, and more code for the same shape.
- **CrewAI**: role-based agents read well in a demo, but control over structured output and over
  deterministic, tokenless steps is weaker.
- **Plain asyncio and google-genai**: the fewest dependencies, but it would re-implement the event
  stream, sessions, tool calling and routing.
- **One large prompt**: the cheapest option, with no parallel research, no independent review and
  nothing to show the user while it runs.
