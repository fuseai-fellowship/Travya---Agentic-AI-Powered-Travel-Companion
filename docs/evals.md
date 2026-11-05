# Evals

The planning agents are measured on a fixed set of golden trips, so changes to prompts, models or
integrations show up as numbers rather than impressions.

## What is measured

`backend/evals/golden_trips.json` holds six trips that stress different paths: a culture trip in
Kathmandu, a short road hop to Pokhara, a food trip in Lisbon, a packed Kyoto itinerary priced in
yen, a three-person New York weekend and a budget-free relaxed trip to Reykjavik.

For each trip the runner calls the real planning service (scouts, planner, critic, quality gate,
reviser) and scores the stored result deterministically:

| Metric | Meaning |
|---|---|
| Plans produced | The stream ended with `done` and a valid `TripPlan` was saved |
| Hard checks | Every trip date covered, no extra dates, activities per day within the pace, total within budget (`agents/planning/checks.py`) |
| Critic approved | The critic's final verdict was "approved" (not just accepted after the revision cap) |
| Revisions | How many times the quality gate sent the plan back |
| Named places on the map | Share of items that name a place and were resolved to coordinates |
| Sources | Cited data sources stored with the plan |
| Latency | Wall-clock time of the whole run |

## Running

```bash
cd backend
uv run python -m evals.run --offline            # fakes and the scripted planner, no keys
uv run python -m evals.run                      # live: needs GEMINI_API_KEY and the database
uv run python -m evals.run --only lisbon-food   # one trip
```

Runs are sequential to stay inside free-tier rate limits. Each run writes a Markdown and a JSON
report to `backend/evals/reports/`.

## Latest live results

Six golden trips, Gemini free tier, public OpenStreetMap, Wikivoyage and Open-Meteo services:

| Metric | Result |
|---|---|
| Plans produced | 6 / 6 |
| Passing all hard checks | 6 / 6 |
| Critic approved | 5 / 6 (Kyoto, "packed" pace, was accepted after the 2-revision cap) |
| Median latency | 32 s |
| Named places on the map | 96 % |

The first live run, before the place resolver and the model fallback changes, produced 5/6 hard
checks, 60 % mapped places and a 40 s median; the reports for both runs are kept in the repository.

## Observability

ADK emits OpenTelemetry spans for every agent run, LLM call and tool call. Set
`ENABLE_CLOUD_TRACE=true` to export them to Cloud Trace, or point the standard
`OTEL_EXPORTER_OTLP_ENDPOINT` variable at any OTLP collector (for example a local Jaeger) to inspect a
planning run step by step (`backend/app/core/telemetry.py`).
