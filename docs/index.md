# Travya

Travya plans trips with a team of AI agents and shows them working. Four research scouts gather
weather, places, guide passages and sample fares in parallel; a planner drafts a day-by-day
itinerary; a critic and a set of deterministic checks review it; a reviser fixes what they find.
Every step streams to the browser, and the result lands on a map built from OpenStreetMap data. In
testing, a live plan took about 35 seconds on free tiers.
Bookings are simulated and always need the traveler's explicit confirmation.

The project was built by Tilak Parajuli during the FuseAI Fellowship, with early UI work by Bigya.

## At a glance

| | |
|---|---|
| Agents | Google ADK 2 `Workflow` graph: 4 concurrent scouts → join → planner → critic → quality gate, which routes to finalize or to the reviser (at most 2 revisions) |
| Model | Gemini Flash with an immediate Flash-Lite fallback, the critic on Flash-Lite; Gemini embeddings for guide retrieval |
| API | FastAPI on Python 3.13, SQLModel, Server-Sent Events, RFC 9457 problem+json errors |
| Data | Postgres 17 with pgvector, Redis for rate limits and the HTTP cache |
| Auth | Firebase Authentication (email/password, Google, anonymous demo) |
| Web | React 19, Vite, TanStack Router and Query, Chakra UI v3, MapLibre with OpenFreeMap tiles |
| Hosting | Hugging Face Spaces (or Cloud Run), Neon, Upstash, Cloudflare Pages, Firebase: free tiers, no card needed |

## Where to start

- **Run it**: [Getting started](getting-started.md) brings up the full stack with one command and no
  API keys.
- **Understand it**: the [architecture overview](architecture/overview.md), then
  [how the agents work](architecture/agents.md).
- **Call it**: the [API reference](api.md) lists every endpoint and the streaming event format.
- **Trust it**: [security](security.md) maps each control to the OWASP API and LLM Top 10 lists.
- **Ship it**: [deployment](operations/deployment.md) and the [runbook](operations/runbook.md).
- **Why it is built this way**: the [architecture decision records](decisions/index.md).

## Repository

The source lives at
[fuseai-fellowship/Travya---Agentic-AI-Powered-Travel-Companion](https://github.com/fuseai-fellowship/Travya---Agentic-AI-Powered-Travel-Companion).
`dev` is the integration branch; `main` is production and deploys on every push.
