"""Runs the planning agents for a trip, streams their activity, and persists the result."""

import asyncio
import re
import uuid
from collections.abc import AsyncGenerator, Iterable
from contextlib import aclosing
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from decimal import Decimal, InvalidOperation
from typing import Any

import anyio
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pydantic import ValidationError
from sqlmodel import col, or_, update
from sqlmodel.ext.asyncio.session import AsyncSession

from app.agents.deadline import deadline_in, until
from app.agents.events import AGENT_LABELS, AgentEvent
from app.agents.planning.pipeline import build_planning_pipeline
from app.core.config import settings
from app.core.db import SessionFactory
from app.core.errors import BudgetExhausted, Conflict
from app.core.logging import get_logger
from app.core.ratelimit import BUDGET_MESSAGE, Limiter
from app.integrations.registry import Integrations
from app.models import Booking, BookingKind, ItemCategory, ItineraryItem, Trip, TripStatus, User
from app.schemas.plan import TripPlan
from app.services.knowledge import KnowledgeService
from app.services.trips import PLANNING_STALE_AFTER, TripService, locate_near

log = get_logger(__name__)

APP_NAME = "travya-planner"
_sessions = InMemorySessionService()  # planning runs are one-shot; nothing to resume

MAX_MONEY = Decimal("9999999999.99")  # NUMERIC(12, 2)
UNAVAILABLE = "Planning failed because an AI or data service is unavailable. Please retry shortly."
INCOMPLETE = "The planner returned an incomplete plan. Please try again."
TOO_SLOW = "The AI models are slow right now and planning ran out of time. Please retry shortly."


class PlanningFailed(Exception):
    """An expected failure; the message is shown to the user."""

    def __init__(self, message: str, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class PlanClaim:
    """A trip reserved for one planning run, and the status to restore if the run fails."""

    trip: Trip
    previous_status: TripStatus


def _time(value: str | None) -> time | None:
    if not value:
        return None
    try:
        return time.fromisoformat(value)
    except ValueError:
        return None


def _money(value: float | None) -> Decimal | None:
    """A non-negative amount that fits the database column, or None."""
    if value is None:
        return None
    try:
        amount = Decimal(str(value)).quantize(Decimal("0.01"))
    except InvalidOperation:
        return None
    return max(amount, Decimal(0)) if amount <= MAX_MONEY else None


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


def _normalise(name: str) -> str:
    words = re.sub(r"[^a-z0-9 ]+", " ", name.casefold()).split()
    return " ".join(w for w in words if w not in {"the", "a", "of", "at", "and"})


class _PlaceResolver:
    """Finds coordinates for planned places: research results first, then a few bounded lookups.

    Lookups go to Photon (no per-second cap, unlike Nominatim), run a few at a time within a
    total time budget, and a failed lookup only leaves that stop off the map.
    """

    MAX_LOOKUPS = 15
    CONCURRENCY = 4
    BUDGET_S = 20.0

    def __init__(
        self, integrations: Integrations, trip: Trip, places: list[dict[str, Any]]
    ) -> None:
        self.integrations = integrations
        self.trip = trip
        self.known: dict[str, tuple[float, float]] = {
            _normalise(p["name"]): (p["lat"], p["lon"])
            for p in places
            if p.get("name") and p.get("lat") is not None and p.get("lon") is not None
        }

    def _match(self, key: str) -> tuple[float, float] | None:
        if key in self.known:
            return self.known[key]
        # The most specific known name that the planned name contains (or is contained in).
        candidates = [
            name
            for name in self.known
            if len(name) >= 5 and len(key) >= 5 and (name in key or key in name)
        ]
        return self.known[max(candidates, key=len)] if candidates else None

    def locate(self, place_name: str | None) -> tuple[float | None, float | None]:
        if not place_name:
            return None, None
        return self._match(_normalise(place_name)) or (None, None)

    async def resolve(self, place_names: Iterable[str | None]) -> None:
        """Looks up the names that research did not cover; call before `locate`."""
        pending: dict[str, str] = {}
        for name in place_names:
            key = _normalise(name or "")
            if key and key not in pending and self._match(key) is None:
                pending[key] = name or ""
        semaphore = asyncio.Semaphore(self.CONCURRENCY)

        async def lookup(key: str, name: str) -> None:
            async with semaphore:
                try:
                    coords = await self._lookup(name)
                except Exception as exc:
                    log.warning("place_lookup_failed", error=type(exc).__name__)
                    return
            if coords:
                self.known[key] = coords

        try:
            async with asyncio.timeout(self.BUDGET_S), asyncio.TaskGroup() as group:
                for key, name in list(pending.items())[: self.MAX_LOOKUPS]:
                    group.create_task(lookup(key, name))
        except TimeoutError:
            log.warning("place_lookup_budget_spent", lookups=len(pending))

    async def _lookup(self, place_name: str) -> tuple[float, float] | None:
        return await locate_near(self.integrations, self.trip, place_name)


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

    async def start(self, trip_id: uuid.UUID) -> PlanClaim:
        """Validates, reserves budget and claims the trip before the stream opens, so errors are
        plain HTTP responses. One run per trip: another gets 409 until it ends or goes stale."""
        trip = await self.trips.get(trip_id)
        previous = trip.status
        now = datetime.now(UTC)
        claimed = (
            await self.session.exec(
                update(Trip)
                .where(
                    col(Trip.id) == trip.id,
                    col(Trip.owner_id) == self.user.id,
                    or_(
                        col(Trip.status) != TripStatus.planning,
                        col(Trip.planning_started_at).is_(None),
                        col(Trip.planning_started_at) < now - PLANNING_STALE_AFTER,
                    ),
                )
                .values(status=TripStatus.planning, planning_started_at=now)
                .returning(col(Trip.id))
            )
        ).first()
        if claimed is None:
            await self.session.rollback()
            raise Conflict("The agents are already planning this trip. Wait for that run to end.")
        try:
            await self.limiter.check_llm_budget()
        except BaseException:
            await self.session.rollback()
            raise
        await self.session.commit()
        return PlanClaim(trip=trip, previous_status=previous)

    async def stream(
        self, claim: PlanClaim, instructions: str | None
    ) -> AsyncGenerator[AgentEvent]:
        """Runs the agents and saves the plan. Whatever happens before the plan is saved (an
        error, a timeout, the client going away), the trip gets its previous status back."""
        trip = claim.trip
        user_id = str(self.user.id)
        adk_session_id: str | None = None
        saved = False
        try:
            yield AgentEvent(
                agent="travya", kind="started", message=f"Planning your trip to {trip.destination}"
            )
            knowledge = KnowledgeService(self.integrations.guides)
            days = (trip.end_date - trip.start_date).days + 1
            pipeline = build_planning_pipeline(
                self.integrations, knowledge, days=days, budget=self.limiter.spend_llm_budget
            )
            runner = Runner(app_name=APP_NAME, node=pipeline, session_service=_sessions)
            adk_session = await _sessions.create_session(
                app_name=APP_NAME,
                user_id=user_id,
                state={"trip": trip_context(trip, instructions)},
            )
            adk_session_id = adk_session.id

            seen: set[str] = set()
            scouts_left = {"weather_scout", "places_scout", "guide_scout", "offers_scout"}
            failures: dict[str, str] = {}  # error code → message
            deadline = deadline_in(settings.PLAN_DEADLINE_SECONDS)
            try:
                async with aclosing(
                    runner.run_async(
                        user_id=user_id,
                        session_id=adk_session.id,
                        new_message=types.Content(
                            role="user", parts=[types.Part(text="Plan this trip.")]
                        ),
                    )
                ) as events:
                    async for event in until(events, deadline):
                        if event.error_code or event.error_message:
                            failures[event.error_code or "error"] = event.error_message or ""
                        for out in self._translate(event, seen):
                            yield out
                            for following in self._next_stage(out, scouts_left, seen):
                                yield following
            except TimeoutError:
                # Keep the latest complete draft if there is one; _plan decides.
                log.warning("plan_deadline", trip_id=str(trip.id))
                failures["deadline"] = ""
            final = await _sessions.get_session(
                app_name=APP_NAME, user_id=user_id, session_id=adk_session.id
            )
            state = dict(final.state) if final else {}
            plan = self._plan(trip.id, state, failures)

            yield AgentEvent(agent="travya", kind="progress", message="Placing stops on the map")
            resolver = _PlaceResolver(self.integrations, trip, state.get("places") or [])
            await resolver.resolve(a.place_name for d in plan.days for a in d.activities)
            items = self._items(trip, plan, resolver)
            quotes = self._quotes(trip, state.get("offers") or [])
            stored_plan = plan.model_dump(mode="json") | {
                "sources": self._sources(state),
                "review": state.get("critique"),
            }
            async with SessionFactory() as session:
                await TripService(session, self.user, self.integrations).replace_agent_output(
                    trip.id, items, quotes, stored_plan
                )
            saved = True
            yield AgentEvent(
                agent="travya",
                kind="done",
                message=f"Your {len(plan.days)}-day itinerary is ready.",
                data={"trip_id": str(trip.id), "items": len(items), "quotes": len(quotes)},
            )
        except PlanningFailed as exc:
            data = {"error": exc.code} if exc.code else None
            yield AgentEvent(agent="travya", kind="error", message=str(exc), data=data)
        except Exception:
            log.exception("plan_failed", trip_id=str(trip.id))
            yield AgentEvent(agent="travya", kind="error", message=UNAVAILABLE)
        finally:
            # Shielded: this also runs when the client goes away and the stream is cancelled.
            with anyio.CancelScope(shield=True):
                if adk_session_id:
                    await _sessions.delete_session(
                        app_name=APP_NAME, user_id=user_id, session_id=adk_session_id
                    )
                if not saved:
                    await self._restore(trip.id, claim.previous_status)

    @staticmethod
    def _plan(trip_id: uuid.UUID, state: dict[str, Any], failures: dict[str, str]) -> TripPlan:
        try:
            return TripPlan.model_validate(state.get("plan"))
        except ValidationError as exc:
            budget = BudgetExhausted.__name__
            if budget in failures:
                raise PlanningFailed(failures[budget] or BUDGET_MESSAGE, code=budget) from exc
            if "deadline" in failures:
                raise PlanningFailed(TOO_SLOW, code="deadline") from exc
            if failures:
                raise PlanningFailed(UNAVAILABLE) from exc
            # Field paths only: the values are model output built from the user's trip.
            fields = sorted({".".join(map(str, e["loc"])) for e in exc.errors()})[:10]
            log.warning(
                "plan_invalid", trip_id=str(trip_id), errors=exc.error_count(), fields=fields
            )
            raise PlanningFailed(INCOMPLETE) from exc

    @staticmethod
    async def _restore(trip_id: uuid.UUID, status: TripStatus) -> None:
        """Puts the trip back unless something else already moved it out of `planning`."""
        try:
            async with SessionFactory() as session:
                await session.exec(
                    update(Trip)
                    .where(col(Trip.id) == trip_id, col(Trip.status) == TripStatus.planning)
                    .values(status=status, planning_started_at=None)
                )
                await session.commit()
        except Exception:
            log.exception("plan_status_not_restored", trip_id=str(trip_id))

    @staticmethod
    def _next_stage(out: AgentEvent, scouts_left: set[str], seen: set[str]) -> list[AgentEvent]:
        """LLM stages emit one final event, so announce each stage as soon as the graph reaches it."""
        follow: str | None = None
        if out.kind == "progress" and out.agent in scouts_left:
            scouts_left.discard(out.agent)
            follow = "planner" if not scouts_left else None
        elif out.kind == "result" and out.agent in ("planner", "reviser"):
            follow = "critic"
        elif out.kind == "result" and out.agent == "critic":
            follow = "quality_gate"
        elif (
            out.kind == "progress"
            and out.agent == "quality_gate"
            and out.message.startswith("Sending")
        ):
            follow = "reviser"
        if follow is None or (follow == "planner" and "planner" in seen):
            return []
        seen.add(follow)
        label = AGENT_LABELS.get(follow, follow)
        return [AgentEvent(agent=follow, kind="started", message=f"{label} started")]

    @staticmethod
    def _translate(event: Event, seen: set[str]) -> list[AgentEvent]:
        author = event.author or "travya"
        if author in ("user", "trip_planner", "research_done", "apply_revision"):
            return []
        label = AGENT_LABELS.get(author, author)
        out: list[AgentEvent] = []
        if author not in seen:
            seen.add(author)
            out.append(AgentEvent(agent=author, kind="started", message=f"{label} started"))
        if event.error_code or event.error_message:
            # The raw message can carry provider internals; the code is enough for the UI.
            code = event.error_code or "error"
            log.warning("agent_error", agent=author, code=code)
            out.append(
                AgentEvent(
                    agent=author,
                    kind="error",
                    message=f"{label} could not finish.",
                    data={"error": code},
                )
            )
            return out
        if not event.is_final_response() or event.partial:
            return out
        delta = event.actions.state_delta if event.actions else {}
        if author == "planner" and isinstance(delta.get("plan"), dict):
            days = delta["plan"].get("days", [])
            count = sum(len(d.get("activities", [])) for d in days)
            out.append(
                AgentEvent(
                    agent=author,
                    kind="result",
                    message=f"Drafted {len(days)} days with {count} activities.",
                )
            )
        elif author == "reviser" and isinstance(delta.get("revision"), dict):
            days = delta["revision"].get("days", [])
            out.append(
                AgentEvent(agent=author, kind="result", message=f"Revised {len(days)} day(s).")
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

    @staticmethod
    def _items(trip: Trip, plan: TripPlan, resolver: _PlaceResolver) -> list[ItineraryItem]:
        items: list[ItineraryItem] = []
        for day in plan.days:
            try:
                day_date = date.fromisoformat(day.date)
            except ValueError:
                continue
            if not trip.start_date <= day_date <= trip.end_date:
                continue
            for position, activity in enumerate(day.activities):
                lat, lon = resolver.locate(activity.place_name)
                place_name = (activity.place_name or "").strip()[:300] or None
                items.append(
                    ItineraryItem(
                        trip_id=trip.id,
                        day=day_date,
                        position=position,
                        start_time=_time(activity.start_time),
                        end_time=_time(activity.end_time),
                        title=activity.title.strip()[:200] or (place_name or "Activity")[:200],
                        description=(activity.description or "")[:2000] or None,
                        category=activity.category
                        if isinstance(activity.category, ItemCategory)
                        else ItemCategory.other,
                        place_name=place_name,
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
        if any(p.get("source") == "wikipedia" for p in state.get("places") or []):
            sources["wikipedia"] = {
                "title": "Wikipedia (CC BY-SA 4.0)",
                "url": "https://en.wikipedia.org/",
            }
        if any(p.get("source") != "wikipedia" for p in state.get("places") or []):
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
