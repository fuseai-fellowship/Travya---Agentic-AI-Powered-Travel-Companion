"""Deterministic plan checks run by the quality gate alongside the LLM critic."""

from datetime import date, timedelta
from typing import Any

from pydantic import ValidationError

from app.schemas.plan import TripPlan

PACE_LIMITS = {"relaxed": (1, 4), "balanced": (2, 6), "packed": (3, 9)}
BUDGET_TOLERANCE = 1.10


def check_plan(raw_plan: dict[str, Any] | None, trip: dict[str, Any]) -> list[str]:
    if not raw_plan:
        return ["The planner produced no plan."]
    try:
        plan = TripPlan.model_validate(raw_plan)
    except ValidationError as exc:
        return [f"The plan does not match the schema: {exc.errors()[0]['msg']}"]

    issues: list[str] = []
    start, end = date.fromisoformat(trip["start_date"]), date.fromisoformat(trip["end_date"])
    expected = {start + timedelta(days=i) for i in range((end - start).days + 1)}
    planned: set[date] = set()
    for day in plan.days:
        try:
            planned.add(date.fromisoformat(day.date))
        except ValueError:
            issues.append(f"Day '{day.date}' is not an ISO date.")
    if missing := sorted(expected - planned):
        issues.append("Missing days: " + ", ".join(d.isoformat() for d in missing))
    if extra := sorted(planned - expected):
        issues.append("Days outside the trip dates: " + ", ".join(d.isoformat() for d in extra))

    low, high = PACE_LIMITS.get(trip.get("pace", "balanced"), (2, 6))
    for day in plan.days:
        sights = [a for a in day.activities if a.category.value != "food"]
        if not low <= len(sights) <= high:
            issues.append(
                f"{day.date} has {len(sights)} non-meal activities; a {trip['pace']} pace needs {low}–{high}."
            )

    if trip.get("budget") and plan.estimated_total:
        limit = float(trip["budget"]) * BUDGET_TOLERANCE
        if plan.estimated_total > limit:
            issues.append(
                f"Estimated total {plan.estimated_total:.0f} exceeds the budget of {float(trip['budget']):.0f}."
            )
    return issues
