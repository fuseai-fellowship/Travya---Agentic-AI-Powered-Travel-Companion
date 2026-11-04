"""The trip-planning multi-agent pipeline on Google ADK.

    SequentialAgent "trip_planner"
    ├── ParallelAgent "research"        weather · places · guide (RAG) · offers   (no LLM)
    ├── LlmAgent "planner"              structured TripPlan → state["plan"]
    └── LoopAgent "refine" (≤ 2 rounds)
        ├── LlmAgent "critic"           structured Critique → state["critique"]
        ├── QualityGate                 critic verdict + deterministic checks; exits the loop when clean
        └── LlmAgent "reviser"          fixes the issues → state["plan"]

Booking is not an agent decision: the offers scout only collects quotes, and the user confirms one
explicitly through the API.
"""

from collections.abc import AsyncGenerator

from google.adk.agents import BaseAgent, LlmAgent, LoopAgent, ParallelAgent, SequentialAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.genai import types

from app.agents.planning.checks import check_plan
from app.agents.planning.prompts import critic_instruction, planner_instruction, reviser_instruction
from app.agents.planning.scouts import build_scouts
from app.core.config import settings
from app.integrations.registry import Integrations
from app.llm.client import SAFETY_SETTINGS, agent_model
from app.schemas.plan import Critique, TripPlan
from app.services.knowledge import KnowledgeService

MAX_REFINE_ROUNDS = 2


class QualityGate(BaseAgent):
    """Merges the critic's verdict with hard checks and ends the refine loop once the plan is clean."""

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event]:
        state = ctx.session.state
        critique = dict(state.get("critique") or {})
        issues = list(critique.get("issues") or []) + check_plan(state.get("plan"), state["trip"])
        approved = bool(critique.get("approved")) and not issues
        rounds = int(state.get("refine_rounds", 0)) + 1
        text = (
            "Plan approved." if approved else f"Sending {len(issues)} issue(s) back to the planner."
        )
        yield Event(
            author=self.name,
            invocation_id=ctx.invocation_id,
            branch=ctx.branch,
            content=types.Content(role="model", parts=[types.Part(text=text)]),
            actions=EventActions(
                state_delta={
                    "critique": {"approved": approved, "issues": issues},
                    "refine_rounds": rounds,
                },
                escalate=approved,
            ),
        )


def _llm(
    name: str,
    description: str,
    instruction: object,
    schema: type,
    output_key: str,
    temperature: float,
) -> LlmAgent:
    return LlmAgent(
        name=name,
        description=description,
        model=agent_model(),
        instruction=instruction,  # type: ignore[arg-type]
        output_schema=schema,
        output_key=output_key,
        include_contents="none",
        generate_content_config=types.GenerateContentConfig(
            temperature=temperature, safety_settings=SAFETY_SETTINGS, max_output_tokens=8192
        ),
    )


def build_planning_pipeline(integrations: Integrations, knowledge: KnowledgeService) -> BaseAgent:
    if settings.OFFLINE_INTEGRATIONS or settings.GEMINI_API_KEY is None:
        from app.agents.planning.offline import ScriptedPlanner

        planner: BaseAgent = ScriptedPlanner(
            name="planner", description="Offline planner for demos and tests"
        )
        return SequentialAgent(
            name="trip_planner",
            sub_agents=[
                ParallelAgent(name="research", sub_agents=build_scouts(integrations, knowledge)),
                planner,
            ],
        )

    return SequentialAgent(
        name="trip_planner",
        description="Researches, drafts and reviews a trip itinerary",
        sub_agents=[
            ParallelAgent(
                name="research",
                description="Gathers weather, places, guide passages and quotes in parallel",
                sub_agents=build_scouts(integrations, knowledge),
            ),
            _llm("planner", "Drafts the itinerary", planner_instruction, TripPlan, "plan", 0.6),
            LoopAgent(
                name="refine",
                description="Critique and revise until the plan passes review",
                max_iterations=MAX_REFINE_ROUNDS,
                sub_agents=[
                    _llm(
                        "critic", "Reviews the draft", critic_instruction, Critique, "critique", 0.1
                    ),
                    QualityGate(name="quality_gate", description="Hard checks and loop exit"),
                    _llm("reviser", "Revises the plan", reviser_instruction, TripPlan, "plan", 0.4),
                ],
            ),
        ],
    )
