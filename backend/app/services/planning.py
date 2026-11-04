"""Runs the planning agents for a trip, streams their activity, and persists the result."""

import uuid
from collections.abc import AsyncIterator
from datetime import date, time
from decimal import Decimal, InvalidOperation
from typing import Any

from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pydantic import ValidationError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.agents.events import AGENT_LABELS, AgentEvent
from app.agents.planning.pipeline import build_planning_pipeline
from app.core.logging import get_logger
from app.core.ratelimit import Limiter
from app.integrations.registry import Integrations
from app.models import Booking, BookingKind, ItemCategory, ItineraryItem, Trip, TripStatus, User
from app.schemas.plan import TripPlan
from app.services.knowledge import KnowledgeService
from app.services.trips import TripService

log = get_logger(__name__)

APP_NAME = "travya-planner"
_sessions = InMemorySessionService()  # planning runs are one-shot; nothing to resume


def _time(value: str | None) -> time | None:
    if not value:
        return None
    try:
        return time.fromisoformat(value)
    except ValueError:
        return None


def _money(value: float | None) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except InvalidOperation:
        return None


def _scout_preview(author: str, delta: dict[str, Any]) -> dict[str, Any] | None:
    """A small slice of each scout's findings so the UI can show research as it lands."""
    if author == "places_scout":
        return {
            "places": [
                {k: p.get(k) for k in ("name", "category", "lat", "lon")}
                for p in (delta.get("places") or [])[:40]
            ]
        }
    if author == "weather_scout":
        return {
            "weather": [
                {
                    k: d.get(k)
                    for k in ("day", "summary", "temp_min_c", "temp_max_c", "weather_code")
                }
                for d in delta.get("weather") or []
            ]
        }
    if author == "guide_scout":
        return {"sources": list(dict.fromkeys(g.get("url") for g in delta.get("guide") or []))[:3]}
    if author == "offers_scout":
        return {"offers": len(delta.get("offers") or [])}
    return None


def trip_context(trip: Trip, instructions: str | None) -> dict[str, Any]:
    return {
        "destination": trip.destination,
        "origin": trip.origin,
        "latitude": trip.latitude,
        "longitude": trip.longitude,
        "start_date": trip.start_date.isoformat(),
        "end_date": trip.end_date.isoformat(),
        "days": (trip.end_date - trip.start_date).days + 1,
        "travelers": trip.travelers,
        "budget": str(trip.budget) if trip.budget is not None else None,
        "currency": trip.currency,
        "pace": trip.pace.value,
        "interests": trip.interests,
        "notes": trip.notes,
        "instructions": instructions,
    }


class PlanningService:
    def __init__(
        self, session: AsyncSession, user: User, integrations: Integrations, limiter: Limiter
    ) -> None:
        self.session = session
        self.user = user
        self.integrations = integrations
        self.limiter = limiter
        self.trips = TripService(session, user, integrations)

    async def start(self, trip_id: uuid.UUID) -> Trip:
        """Validate and reserve budget before the stream opens, so errors are plain HTTP responses."""
        trip = await self.trips.get(trip_id)
        await self.limiter.spend_llm_budget()
        return trip

    async def stream(self, trip: Trip, instructions: str | None) -> AsyncIterator[AgentEvent]:
        previous_status = trip.status
        await self.trips.trips.update(trip, {"status": TripStatus.planning})
        await self.session.commit()

        knowledge = KnowledgeService(self.session, self.integrations.guides)
        pipeline = build_planning_pipeline(self.integrations, knowledge)
        runner = Runner(app_name=APP_NAME, agent=pipeline, session_service=_sessions)
        adk_session = await _sessions.create_session(
            app_name=APP_NAME,
            user_id=str(self.user.id),
            state={"trip": trip_context(trip, instructions)},
        )
        yield AgentEvent(
            agent="travya", kind="started", message=f"Planning your trip to {trip.destination}"
        )

        seen: set[str] = set()
        try:
            async for event in runner.run_async(
                user_id=str(self.user.id),
                session_id=adk_session.id,
                new_message=types.Content(role="user", parts=[types.Part(text="Plan this trip.")]),
            ):
                for out in self._translate(event, seen):
                    yield out
            final = await _sessions.get_session(
                app_name=APP_NAME, user_id=str(self.user.id), session_id=adk_session.id
            )
            state = dict(final.state) if final else {}
            plan = TripPlan.model_validate(state.get("plan"))
        except (ValidationError, TypeError) as exc:
            log.warning("plan_invalid", trip_id=str(trip.id), error=str(exc))
            await self._restore(trip, previous_status)
            yield AgentEvent(
                agent="travya",
                kind="error",
                message="The planner returned an incomplete plan. Please try again.",
            )
            return
        except Exception as exc:
            log.exception("plan_failed", trip_id=str(trip.id))
            await self._restore(trip, previous_status)
            yield AgentEvent(
                agent="travya",
                kind="error",
                message="Planning failed because an AI or data service is unavailable. Please retry shortly.",
                data={"error": type(exc).__name__},
            )
            return
        finally:
            await _sessions.delete_session(
                app_name=APP_NAME, user_id=str(self.user.id), session_id=adk_session.id
            )

        items = await self._items(trip, plan, state.get("places") or [])
        quotes = self._quotes(trip, state.get("offers") or [])
        stored_plan = plan.model_dump(mode="json") | {
            "sources": self._sources(state),
            "review": state.get("critique"),
        }
        await self.trips.replace_agent_output(trip, items, quotes, stored_plan)
        yield AgentEvent(
            agent="travya",
            kind="done",
            message=f"Your {len(plan.days)}-day itinerary is ready.",
            data={"trip_id": str(trip.id), "items": len(items), "quotes": len(quotes)},
        )

    async def _restore(self, trip: Trip, status: TripStatus) -> None:
        await self.session.rollback()
        await self.session.refresh(trip)
        await self.trips.trips.update(trip, {"status": status})
        await self.session.commit()

    @staticmethod
    def _translate(event: Event, seen: set[str]) -> list[AgentEvent]:
        author = event.author or "travya"
        if author == "user":
            return []
        label = AGENT_LABELS.get(author, author)
        out: list[AgentEvent] = []
        if author not in seen:
            seen.add(author)
            out.append(AgentEvent(agent=author, kind="started", message=f"{label} started"))
        if event.error_message:
            out.append(AgentEvent(agent=author, kind="error", message=event.error_message))
            return out
        if not event.is_final_response() or event.partial:
            return out
        delta = event.actions.state_delta if event.actions else {}
        if author in ("planner", "reviser") and isinstance(delta.get("plan"), dict):
            days = delta["plan"].get("days", [])
            count = sum(len(d.get("activities", [])) for d in days)
            verb = "Revised" if author == "reviser" else "Drafted"
            out.append(
                AgentEvent(
                    agent=author,
                    kind="result",
                    message=f"{verb} {len(days)} days with {count} activities.",
                )
            )
        elif author == "critic" and isinstance(delta.get("critique"), dict):
            issues = delta["critique"].get("issues", [])
            message = "Looks good." if not issues else f"Found {len(issues)} thing(s) to improve."
            out.append(
                AgentEvent(
                    agent=author, kind="result", message=message, data={"issues": issues[:5]}
                )
            )
        else:
            text = (
                "".join(p.text or "" for p in (event.content.parts or [])) if event.content else ""
            )
            if text and author != "planner":
                out.append(
                    AgentEvent(
                        agent=author,
                        kind="progress",
                        message=text[:300],
                        data=_scout_preview(author, delta),
                    )
                )
        return out

    async def _items(
        self, trip: Trip, plan: TripPlan, places: list[dict[str, Any]]
    ) -> list[ItineraryItem]:
        coords = {p["name"].strip().lower(): (p["lat"], p["lon"]) for p in places if p.get("name")}
        geocoded = 0
        items: list[ItineraryItem] = []
        for day in plan.days:
            try:
                day_date = date.fromisoformat(day.date)
            except ValueError:
                continue
            if not trip.start_date <= day_date <= trip.end_date:
                continue
            for position, activity in enumerate(day.activities):
                lat = lon = None
                if activity.place_name:
                    key = activity.place_name.strip().lower()
                    if key in coords:
                        lat, lon = coords[key]
                    elif geocoded < 12:
                        geocoded += 1
                        matches = await self.integrations.geocoder.search(
                            f"{activity.place_name}, {trip.destination}", limit=1
                        )
                        if matches:
                            lat, lon = matches[0].lat, matches[0].lon
                            coords[key] = (lat, lon)
                items.append(
                    ItineraryItem(
                        trip_id=trip.id,
                        day=day_date,
                        position=position,
                        start_time=_time(activity.start_time),
                        end_time=_time(activity.end_time),
                        title=activity.title[:200],
                        description=(activity.description or "")[:2000] or None,
                        category=activity.category
                        if isinstance(activity.category, ItemCategory)
                        else ItemCategory.other,
                        place_name=(activity.place_name or "")[:300] or None,
                        latitude=lat,
                        longitude=lon,
                        estimated_cost=_money(activity.estimated_cost),
                        source="agent",
                    )
                )
        return items

    @staticmethod
    def _quotes(trip: Trip, offers: list[dict[str, Any]]) -> list[Booking]:
        quotes = []
        for offer in offers[:8]:
            amount = _money(offer.get("amount"))
            if amount is None or offer.get("kind") not in ("flight", "hotel"):
                continue
            quotes.append(
                Booking(
                    trip_id=trip.id,
                    kind=BookingKind(offer["kind"]),
                    title=str(offer.get("title", ""))[:200],
                    provider=str(offer.get("provider", ""))[:120],
                    details=offer.get("details") or {},
                    amount=amount,
                    currency=str(offer.get("currency") or trip.currency)[:3],
                )
            )
        return quotes

    @staticmethod
    def _sources(state: dict[str, Any]) -> list[dict[str, str]]:
        sources: dict[str, dict[str, str]] = {}
        for snippet in state.get("guide") or []:
            url = snippet.get("url")
            if url and url not in sources:
                sources[url] = {
                    "title": f"{snippet.get('source', 'guide').capitalize()} travel guide",
                    "url": url,
                }
        if state.get("places"):
            sources["osm"] = {
                "title": "OpenStreetMap contributors",
                "url": "https://www.openstreetmap.org/copyright",
            }
        if state.get("weather"):
            sources["open-meteo"] = {
                "title": "Open-Meteo weather data",
                "url": "https://open-meteo.com/",
            }
        return list(sources.values())
