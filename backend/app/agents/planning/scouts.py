"""Research scouts: deterministic agents that gather data in parallel (no LLM tokens spent).

Each writes its findings to session state through `state_delta` and reports progress as an event.
A failing scout never fails the plan; it reports what is missing and the planner works without it.
"""

import asyncio
from collections.abc import AsyncGenerator, Awaitable, Callable
from datetime import date
from decimal import Decimal
from typing import Any

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.genai import types
from pydantic import PrivateAttr

from app.core.logging import get_logger
from app.integrations.geo import haversine_m
from app.integrations.ports import GeoPoint, PoiCategory
from app.integrations.registry import Integrations
from app.services.knowledge import KnowledgeService

log = get_logger(__name__)

INTEREST_CATEGORIES: dict[str, list[PoiCategory]] = {
    "culture": ["museum", "attraction", "religious"],
    "history": ["museum", "attraction", "religious"],
    "food": ["restaurant", "cafe"],
    "nature": ["park", "viewpoint"],
    "adventure": ["viewpoint", "park", "attraction"],
    "nightlife": ["nightlife"],
    "shopping": ["shopping"],
    "relaxation": ["park", "cafe"],
    "photography": ["viewpoint", "attraction"],
    "family": ["park", "attraction", "museum"],
}

SCOUT_BUDGET_S = 30.0
SHORT_HOP_KM = 250.0  # below this, road travel beats flying

Finding = tuple[str, dict[str, Any]]  # (progress message, state delta)


class Scout(BaseAgent):
    _work: Callable[[dict[str, Any]], Awaitable[Finding]] = PrivateAttr()
    _fallback: dict[str, Any] = PrivateAttr()

    @classmethod
    def build(
        cls,
        name: str,
        description: str,
        work: Callable[[dict[str, Any]], Awaitable[Finding]],
        fallback: dict[str, Any],
    ) -> "Scout":
        scout = cls(name=name, description=description)
        scout._work = work
        scout._fallback = fallback
        return scout

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event]:
        trip = ctx.session.state["trip"]
        # A partial event marks the start, so the UI can time each scout.
        yield Event(
            author=self.name,
            invocation_id=ctx.invocation_id,
            branch=ctx.branch,
            partial=True,
            content=types.Content(role="model", parts=[types.Part(text="Working…")]),
        )
        try:
            async with asyncio.timeout(SCOUT_BUDGET_S):
                message, delta = await self._work(trip)
        except Exception as exc:  # a scout must never sink the whole plan
            log.warning("scout_failed", scout=self.name, error=type(exc).__name__)
            message, delta = (
                f"Could not reach this source ({type(exc).__name__}); continuing without it.",
                self._fallback,
            )
        yield Event(
            author=self.name,
            invocation_id=ctx.invocation_id,
            branch=ctx.branch,
            content=types.Content(role="model", parts=[types.Part(text=message)]),
            actions=EventActions(state_delta=delta),
        )


def _center(trip: dict[str, Any]) -> GeoPoint | None:
    if trip.get("latitude") is None or trip.get("longitude") is None:
        return None
    return GeoPoint(lat=trip["latitude"], lon=trip["longitude"])


def build_scouts(integrations: Integrations, knowledge: KnowledgeService) -> list[BaseAgent]:
    async def _distance_km(trip: dict[str, Any]) -> float | None:
        center = _center(trip)
        if not trip.get("origin") or center is None:
            return None
        origin = await integrations.geocoder.search(trip["origin"], limit=1)
        if not origin:
            return None
        return haversine_m(origin[0].lat, origin[0].lon, center.lat, center.lon) / 1000

    async def weather(trip: dict[str, Any]) -> Finding:
        center = _center(trip)
        if center is None:
            return "No coordinates for the destination, so no forecast.", {"weather": []}
        days = await integrations.weather.daily(
            center, date.fromisoformat(trip["start_date"]), date.fromisoformat(trip["end_date"])
        )
        data = [d.model_dump(mode="json") for d in days]
        if not days:
            return "No weather data for these dates.", {"weather": []}
        low = min(d.temp_min_c for d in days)
        high = max(d.temp_max_c for d in days)
        wet = sum(1 for d in days if d.precipitation_mm >= 5)
        kind = "climate averages" if any(d.is_climate_estimate for d in days) else "forecast"
        return f"Weather {kind}: {low:.0f}–{high:.0f}°C, {wet} rainy day(s).", {"weather": data}

    async def places(trip: dict[str, Any]) -> Finding:
        center = _center(trip)
        if center is None:
            return "No coordinates for the destination, so no nearby places.", {"places": []}
        categories: list[PoiCategory] = ["attraction", "museum", "viewpoint", "restaurant"]
        for interest in trip.get("interests") or []:
            categories.extend(INTEREST_CATEGORIES.get(interest.lower(), []))
        found = await integrations.places.nearby(
            center, categories=list(dict.fromkeys(categories)), radius_m=6000, limit=45
        )
        data = [
            p.model_dump(
                include={"name", "category", "lat", "lon", "opening_hours", "address", "source"}
            )
            for p in found
        ]
        source = (
            "Wikipedia"
            if found and all(p.source == "wikipedia" for p in found)
            else "OpenStreetMap"
        )
        return f"Found {len(found)} places on {source}.", {"places": data}

    async def guide(trip: dict[str, Any]) -> Finding:
        destination = trip["destination"]
        guide_url = await knowledge.ensure_indexed(destination)
        if not guide_url:
            return f"No travel guide found for {destination}.", {"guide": []}
        query = (
            f"Best things to do, food, getting around and safety for a {trip['pace']} trip; interests: "
            + (", ".join(trip.get("interests") or []) or "sightseeing")
        )
        snippets = await knowledge.search(guide_url, query, k=8)
        data = [
            {"title": s.title, "text": s.text, "url": s.url, "source": s.source} for s in snippets
        ]
        source = snippets[0].source.capitalize() if snippets else "guide"
        return f"Read {len(snippets)} relevant passages from {source}.", {"guide": data}

    async def offers(trip: dict[str, Any]) -> Finding:
        start, end = date.fromisoformat(trip["start_date"]), date.fromisoformat(trip["end_date"])
        nights = max(1, (end - start).days)
        budget = Decimal(str(trip["budget"])) if trip.get("budget") else None
        nightly = (budget * Decimal("0.4") / nights).quantize(Decimal("0.01")) if budget else None
        hotels = await integrations.offers.hotels(
            destination=trip["destination"],
            check_in=start,
            check_out=end,
            travelers=trip["travelers"],
            nightly_budget=nightly,
            currency=trip["currency"],
        )
        flights = []
        distance_km = await _distance_km(trip)
        if trip.get("origin") and (distance_km is None or distance_km >= SHORT_HOP_KM):
            flights = await integrations.offers.flights(
                origin=trip["origin"],
                destination=trip["destination"],
                depart=start,
                return_date=end,
                travelers=trip["travelers"],
                currency=trip["currency"],
                distance_km=distance_km,
            )
        data = [o.model_dump(mode="json") for o in [*flights, *hotels]]
        if not trip.get("origin"):
            return (
                f"Found {len(hotels)} stays (sample fares). Add a starting city for flight quotes.",
                {"offers": data},
            )
        if not flights:
            return (
                f"Found {len(hotels)} stays; {trip['origin']} is close enough to travel by road.",
                {"offers": data},
            )
        return (
            f"Found {len(hotels)} stays and {len(flights)} flights (sample fares, booking is simulated).",
            {"offers": data},
        )

    return [
        Scout.build(
            "weather_scout", "Fetches the forecast or climate averages", weather, {"weather": []}
        ),
        Scout.build(
            "places_scout", "Finds points of interest on OpenStreetMap", places, {"places": []}
        ),
        Scout.build("guide_scout", "Retrieves destination guide passages", guide, {"guide": []}),
        Scout.build(
            "offers_scout", "Collects sample flight and stay quotes", offers, {"offers": []}
        ),
    ]
