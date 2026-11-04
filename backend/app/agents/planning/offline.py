"""A deterministic planner used without a Gemini key (tests, offline demos).

It builds a plausible itinerary from the research scouts' findings so the full flow, from research
to persistence, map and bookings, works end to end without any model call.
"""

from collections.abc import AsyncGenerator
from datetime import date, timedelta
from typing import Any

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.genai import types

from app.agents.planning.checks import PACE_LIMITS
from app.models import ItemCategory
from app.schemas.plan import BudgetBreakdown, PlannedActivity, PlannedDay, TripPlan

SLOTS = ["09:00", "11:00", "14:00", "16:00", "18:00", "20:00", "21:30"]


def scripted_plan(trip: dict[str, Any], places: list[dict[str, Any]]) -> TripPlan:
    start, end = date.fromisoformat(trip["start_date"]), date.fromisoformat(trip["end_date"])
    per_day = PACE_LIMITS.get(trip.get("pace", "balanced"), (2, 6))[0] + 1
    sights = [p for p in places if p.get("category") not in ("restaurant", "cafe")] or [
        {"name": f"{trip['destination']} old town", "category": "attraction"}
    ]
    food = [p for p in places if p.get("category") in ("restaurant", "cafe")]
    days: list[PlannedDay] = []
    for offset in range((end - start).days + 1):
        current = start + timedelta(days=offset)
        activities = []
        for i in range(per_day):
            place = sights[(offset * per_day + i) % len(sights)]
            activities.append(
                PlannedActivity(
                    start_time=SLOTS[i],
                    end_time=SLOTS[i + 1] if i + 1 < len(SLOTS) else None,
                    title=f"Visit {place['name']}",
                    description=f"Explore {place['name']} at an easy pace.",
                    category=ItemCategory.sight,
                    place_name=place["name"],
                    estimated_cost=10.0,
                )
            )
        if food:
            meal = food[offset % len(food)]
            activities.append(
                PlannedActivity(
                    start_time="19:30",
                    title=f"Dinner at {meal['name']}",
                    description="A local favourite near the day's last stop.",
                    category=ItemCategory.food,
                    place_name=meal["name"],
                    estimated_cost=25.0,
                )
            )
        days.append(
            PlannedDay(
                date=current.isoformat(),
                theme=f"Day {offset + 1} in {trip['destination']}",
                activities=activities,
            )
        )
    total = sum(a.estimated_cost or 0 for d in days for a in d.activities)
    return TripPlan(
        summary=f"A {trip['pace']} {len(days)}-day trip to {trip['destination']} built offline from OpenStreetMap data.",
        days=days,
        estimated_total=total,
        budget_breakdown=BudgetBreakdown(activities=total),
        packing_tips=["Comfortable walking shoes", "Reusable water bottle"],
        local_tips=["Check opening hours before you go."],
    )


class ScriptedPlanner(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event]:
        state = ctx.session.state
        plan = scripted_plan(state["trip"], list(state.get("places") or []))
        yield Event(
            author=self.name,
            invocation_id=ctx.invocation_id,
            branch=ctx.branch,
            content=types.Content(role="model", parts=[types.Part(text=plan.model_dump_json())]),
            actions=EventActions(state_delta={"plan": plan.model_dump(mode="json")}),
        )
