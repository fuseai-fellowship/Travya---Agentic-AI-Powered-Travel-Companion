# Research

[**Travya: Agentic AI-Powered Travel Companion: literature review**](research/literature-review.pdf)
(PDF), by Tilak Parajuli and Bigya Vijay Dhungana, FuseAI Fellowship 2025.

The review surveys AI travel planners in industry (Layla, GuideGeek, Mindtrip and others), academic
work on LLM-based and agentic travel planning, multi-agent orchestration and retrieval-augmented
generation, and the open challenges: reliability, privacy, trust and user agency.

## How it shaped the build

- **Generate, then verify.** The literature on LLM planning (for example the LLM-Modulo line of work on
  travel planning) argues that a model's plan should be checked by external verifiers rather than
  trusted. Travya's refine loop does this: an LLM critic plus deterministic checks for dates, pace and
  budget, with the issues fed back to a reviser
  ([Agents](architecture/agents.md#quality-gate-and-deterministic-checks)).
- **Grounding.** Plans are built from fetched data (OpenStreetMap places, Wikivoyage passages,
  Open-Meteo weather), and every plan stores its sources.
- **User agency.** The agents propose; the traveler edits the itinerary and confirms any booking
  ([ADR 0006](decisions/0006-simulated-bookings-human-in-the-loop.md)).

## Proposal and implementation

The review was written as the fellowship proposal, before the rebuild. Its target architecture
(Vertex AI, multi-modal input, real booking and payment integrations, production-scale availability and
budget) describes an ambition, not this repository. The system as built runs on free tiers with open
data and simulated bookings; the [architecture decisions](decisions/index.md) record why.
