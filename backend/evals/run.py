"""Planning evals: run the agent pipeline on golden trips and score the results.

    uv run python -m evals.run                 # all trips, real services (needs GEMINI_API_KEY + database)
    uv run python -m evals.run --only lisbon-food --offline

Scores are deterministic: the plan's hard checks (dates, pace, budget), whether the critic approved,
revisions used, places with coordinates, cited sources and latency. A Markdown and a JSON report are
written to evals/reports/.
"""

import argparse
import asyncio
import json
import os
import statistics
import time
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

HERE = Path(__file__).parent


async def run_case(case: dict[str, Any], start: date) -> dict[str, Any]:
    from app.agents.planning.checks import check_plan
    from app.core.config import settings
    from app.core.db import SessionFactory
    from app.core.ratelimit import Limiter
    from app.core.security import Principal
    from app.integrations.http import create_http_client
    from app.integrations.registry import build_integrations
    from app.models import Trip
    from app.repositories import ItineraryRepository
    from app.schemas.trips import TripCreate
    from app.services.planning import PlanningService, trip_context
    from app.services.trips import TripService
    from app.services.users import get_or_create_user

    http = create_http_client(settings)
    integrations = build_integrations(settings, http)
    try:
        async with SessionFactory() as session:
            user = await get_or_create_user(
                session, Principal("evals", None, "Evals", False, False)
            )
            trip = await TripService(session, user, integrations).create(
                TripCreate(
                    title=f"Eval: {case['id']}",
                    destination=case["destination"],
                    origin=case.get("origin"),
                    start_date=start,
                    end_date=start + timedelta(days=case["days"] - 1),
                    travelers=case["travelers"],
                    budget=Decimal(str(case["budget"])) if case.get("budget") else None,
                    currency=case["currency"],
                    pace=case["pace"],
                    interests=case["interests"],
                )
            )
            planner = PlanningService(session, user, integrations, Limiter("async+memory://"))
            started = time.perf_counter()
            events = [e async for e in planner.stream(trip, None)]
            seconds = time.perf_counter() - started
            await session.refresh(trip)
            items = await ItineraryRepository(session, trip.id).all()
            plan = trip.plan or {}
            result = {
                "id": case["id"],
                "ok": events[-1].kind == "done",
                "seconds": round(seconds, 1),
                "hard_check_issues": check_plan(
                    {k: v for k, v in plan.items() if k not in ("sources", "review")} or None,
                    trip_context(trip, None),
                ),
                "critic_approved": bool((plan.get("review") or {}).get("approved")),
                "revisions": sum(1 for e in events if e.agent == "reviser" and e.kind == "result"),
                "items": len(items),
                "mapped_share": round(
                    sum(1 for i in items if i.latitude is not None) / max(1, len(items)), 2
                ),
                "sources": len(plan.get("sources") or []),
                "error": next((e.message for e in events if e.kind == "error"), None),
            }
            await session.delete(await session.get(Trip, trip.id))
            await session.commit()
            return result
    finally:
        await http.aclose()


def report(results: list[dict[str, Any]], offline: bool) -> str:
    ok = [r for r in results if r["ok"]]
    lines = [
        f"# Planning evals — {datetime.now(UTC):%Y-%m-%d %H:%M} UTC ({'offline' if offline else 'live'})",
        "",
        f"- Plans produced: **{len(ok)}/{len(results)}**",
        f"- Passing all hard checks: **{sum(1 for r in ok if not r['hard_check_issues'])}/{len(ok)}**",
        f"- Critic approved: **{sum(1 for r in ok if r['critic_approved'])}/{len(ok)}**",
        f"- Median latency: **{statistics.median([r['seconds'] for r in ok]) if ok else 0:.1f} s**",
        f"- Mean share of mapped items: **{statistics.mean([r['mapped_share'] for r in ok]) if ok else 0:.0%}**",
        "",
        "| trip | ok | s | hard-check issues | critic | revisions | items | mapped | sources |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {r['id']} | {'yes' if r['ok'] else 'no'} | {r['seconds']} | {len(r['hard_check_issues'])} "
            f"| {'approved' if r['critic_approved'] else '-'} | {r['revisions']} | {r['items']} "
            f"| {r['mapped_share']:.0%} | {r['sources']} |"
        )
    failures = [(r["id"], i) for r in results for i in r["hard_check_issues"]]
    if failures:
        lines += ["", "## Hard-check issues", *[f"- {trip}: {issue}" for trip, issue in failures]]
    return "\n".join(lines) + "\n"


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", nargs="*", help="trip ids to run")
    parser.add_argument("--offline", action="store_true", help="fakes and the scripted planner")
    args = parser.parse_args()
    if args.offline:
        os.environ["OFFLINE_INTEGRATIONS"] = "true"
    from cashews import cache

    from app.core.config import settings

    cache.setup(settings.REDIS_URL or "mem://")
    cases = json.loads((HERE / "golden_trips.json").read_text())
    if args.only:
        cases = [c for c in cases if c["id"] in args.only]
    start = date.today() + timedelta(days=10)  # inside the 16-day forecast window
    results = []
    for case in cases:  # sequential: free-tier rate limits
        print(f"→ {case['id']}", flush=True)
        results.append(await run_case(case, start))
    out = HERE / "reports"
    out.mkdir(exist_ok=True)
    stamp = f"{datetime.now(UTC):%Y%m%d-%H%M}"
    markdown = report(results, args.offline)
    (out / f"{stamp}.md").write_text(markdown)
    (out / f"{stamp}.json").write_text(json.dumps(results, indent=2, default=str))
    print(markdown)


if __name__ == "__main__":
    asyncio.run(main())
