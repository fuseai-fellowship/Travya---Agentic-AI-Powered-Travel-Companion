"""The trip-planning multi-agent graph on Google ADK Workflow.

    START ─┬─ weather_scout ─┐
           ├─ places_scout  ─┤
           ├─ guide_scout   ─┼─ research_done ─ planner ─ critic ─ quality_gate ─┬─ "approved" → finalize
           └─ offers_scout  ─┘                                ▲                 └─ "revise"   → reviser
                                                              └──── apply_revision ◀──────────────┘

- Scouts run concurrently and use no LLM tokens; the join waits for all four.
- The planner emits a structured TripPlan, the critic a Critique, and the reviser a PlanRevision
  holding only the days it changed, which apply_revision merges into the plan. Output size (and
  time) for a revision therefore does not grow with the trip's length.
- The quality gate merges the critic's verdict with deterministic checks and routes back to the
  reviser at most MAX_REVISIONS times.

Booking is not an agent decision: the offers scout only collects quotes, and the user confirms one
explicitly through the API.
"""

from collections.abc import AsyncGenerator, Awaitable, Callable
from datetime import date
from typing import Any

from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.events import Event, EventActions
from google.adk.workflow import START, JoinNode, Workflow
from google.genai import types

from app.agents.planning.checks import check_plan
from app.agents.planning.prompts import critic_instruction, planner_instruction, reviser_instruction
from app.agents.planning.scouts import build_scouts
from app.core.config import settings
from app.integrations.registry import Integrations
from app.llm.client import SAFETY_SETTINGS, agent_model, http_options
from app.schemas.plan import Critique, PlanRevision, TripPlan
from app.services.knowledge import KnowledgeService

MAX_REVISIONS = 2


def _say(agent: BaseAgent, ctx: InvocationContext, text: str, actions: EventActions) -> Event:
    return Event(
        author=agent.name,
        invocation_id=ctx.invocation_id,
        branch=ctx.branch,
        content=types.Content(role="model", parts=[types.Part(text=text)]),
        actions=actions,
    )


class QualityGate(BaseAgent):
    """Merges the critic's verdict with hard checks and routes to the reviser or to finalize."""

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event]:
        state = ctx.session.state
        critique = dict(state.get("critique") or {})
        issues = list(critique.get("issues") or []) + check_plan(state.get("plan"), state["trip"])
        approved = bool(critique.get("approved")) and not issues
        revisions = int(state.get("revisions", 0))
        if approved:
            route, text = "approved", "Plan approved."
        elif revisions >= MAX_REVISIONS:
            route, text = (
                "approved",
                f"Accepted after {revisions} revisions; {len(issues)} note(s) kept.",
            )
        else:
            route, text = "revise", f"Sending {len(issues)} issue(s) back to the planner."
        yield _say(
            self,
            ctx,
            text,
            EventActions(
                state_delta={
                    "critique": {"approved": approved, "issues": issues},
                    "revisions": revisions + (route == "revise"),
                },
                route=route,
            ),
        )


def merge_revision(
    plan: dict[str, Any] | None, revision: dict[str, Any] | None, trip: dict[str, Any]
) -> dict[str, Any]:
    """The plan with the revised days swapped in; days outside the trip dates are dropped."""
    merged = dict(plan or {})
    if not isinstance(revision, dict):
        return merged
    start, end = trip["start_date"], trip["end_date"]
    days = {d.get("date"): d for d in merged.get("days") or [] if isinstance(d, dict)}
    for day in revision.get("days") or []:
        if isinstance(day, dict) and day.get("date"):
            days[day["date"]] = day
    merged["days"] = sorted(
        (d for key, d in days.items() if isinstance(key, str) and _within(key, start, end)),
        key=lambda d: str(d["date"]),
    )
    for field in ("summary", "estimated_total", "budget_breakdown", "packing_tips", "local_tips"):
        if revision.get(field) not in (None, "", [], {}):
            merged[field] = revision[field]
    return merged


def _within(day: str, start: str, end: str) -> bool:
    try:
        return date.fromisoformat(start) <= date.fromisoformat(day) <= date.fromisoformat(end)
    except ValueError:
        return False


class ApplyRevision(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event]:
        state = ctx.session.state
        revision = state.get("revision") or {}
        plan = merge_revision(state.get("plan"), revision, state["trip"])
        changed = len(revision.get("days") or [])
        yield _say(
            self,
            ctx,
            f"Applied {changed} revised day(s).",
            EventActions(state_delta={"plan": plan}),
        )


class Finalize(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event]:
        yield _say(self, ctx, "Itinerary finalised.", EventActions())


# Room for a 21-day plan (~600 tokens a day) plus the model's thinking, which counts too.
MAX_OUTPUT_TOKENS = 32_768


def _llm(
    name: str,
    description: str,
    instruction: Callable[[ReadonlyContext], str],
    schema: type,
    output_key: str,
    temperature: float,
    *,
    light: bool = False,
    timeout_s: float = 90.0,
    max_output_tokens: int = MAX_OUTPUT_TOKENS,
    budget: Callable[[], Awaitable[None]] | None = None,
) -> LlmAgent:
    return LlmAgent(
        name=name,
        description=description,
        model=agent_model(light=light, budget=budget),
        instruction=instruction,
        output_schema=schema,
        output_key=output_key,
        include_contents="none",
        generate_content_config=types.GenerateContentConfig(
            temperature=temperature,
            safety_settings=SAFETY_SETTINGS,
            max_output_tokens=max_output_tokens,
            http_options=http_options(timeout_s),
        ),
    )


def planner_timeout_s(days: int) -> float:
    """The draft grows with the trip: about five seconds of generation per day."""
    return max(90.0, 40.0 + 5.0 * days)


def build_planning_pipeline(
    integrations: Integrations,
    knowledge: KnowledgeService,
    *,
    days: int = 7,
    budget: Callable[[], Awaitable[None]] | None = None,
) -> Workflow:
    scouts = tuple(build_scouts(integrations, knowledge))
    research_done = JoinNode(name="research_done")

    if settings.OFFLINE_INTEGRATIONS or not settings.gemini_api_keys():
        from app.agents.planning.offline import ScriptedPlanner

        planner = ScriptedPlanner(name="planner", description="Offline planner for demos and tests")
        return Workflow(name="trip_planner", edges=[(START, scouts, research_done, planner)])

    planner_llm = _llm(
        "planner",
        "Drafts the itinerary",
        planner_instruction,
        TripPlan,
        "plan",
        0.6,
        timeout_s=planner_timeout_s(days),
        budget=budget,
    )
    critic = _llm(
        "critic",
        "Reviews the draft",
        critic_instruction,
        Critique,
        "critique",
        0.1,
        light=True,
        timeout_s=60,
        max_output_tokens=8192,
        budget=budget,
    )
    reviser = _llm(
        "reviser",
        "Revises the days with issues",
        reviser_instruction,
        PlanRevision,
        "revision",
        0.4,
        budget=budget,
    )
    apply = ApplyRevision(name="apply_revision", description="Merges revised days into the plan")
    gate = QualityGate(name="quality_gate", description="Hard checks and routing")
    finalize = Finalize(name="finalize", description="Marks the plan as final")
    return Workflow(
        name="trip_planner",
        description="Researches, drafts and reviews a trip itinerary",
        edges=[
            (START, scouts, research_done, planner_llm, critic, gate),
            (gate, {"approved": finalize, "revise": reviser}),
            (reviser, apply, critic),
        ],
    )
