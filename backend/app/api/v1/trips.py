import uuid
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sse_starlette import EventSourceResponse, ServerSentEvent

from app.api.deps import CurrentUser, IntegrationsDep, LimiterDep, SessionDep, rate_limit
from app.core.config import settings
from app.models import TripStatus
from app.schemas.common import Page
from app.schemas.content import WeatherDay
from app.schemas.maps import TripMap
from app.schemas.trips import (
    BookingRead,
    ItineraryItemCreate,
    ItineraryItemRead,
    ItineraryItemUpdate,
    PhotoRead,
    PlanRequest,
    TripCreate,
    TripDetail,
    TripRead,
    TripUpdate,
)
from app.services.planning import PlanningService
from app.services.trips import TripService

router = APIRouter(prefix="/trips", tags=["trips"])


def get_service(
    session: SessionDep, user: CurrentUser, integrations: IntegrationsDep
) -> TripService:
    return TripService(session, user, integrations)


Service = Annotated[TripService, Depends(get_service)]


@router.get("", response_model=Page[TripRead])
async def list_trips(
    service: Service,
    status_: Annotated[TripStatus | None, Query(alias="status")] = None,
    q: Annotated[str | None, Query(max_length=100)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[TripRead]:
    trips, total = await service.page(status=status_, query=q, limit=limit, offset=offset)
    return Page(
        items=[TripRead.model_validate(t) for t in trips], total=total, limit=limit, offset=offset
    )


@router.post("", response_model=TripDetail, status_code=status.HTTP_201_CREATED)
async def create_trip(data: TripCreate, service: Service) -> TripDetail:
    return TripDetail.model_validate(await service.create(data))


@router.get("/{trip_id}", response_model=TripDetail)
async def get_trip(trip_id: uuid.UUID, service: Service) -> TripDetail:
    return TripDetail.model_validate(await service.get(trip_id))


@router.patch("/{trip_id}", response_model=TripDetail)
async def update_trip(trip_id: uuid.UUID, data: TripUpdate, service: Service) -> TripDetail:
    return TripDetail.model_validate(await service.update(trip_id, data))


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trip(trip_id: uuid.UUID, service: Service) -> None:
    await service.delete(trip_id)


@router.post(
    "/{trip_id}/plan",
    summary="Plan the trip with the agents (Server-Sent Events)",
    response_class=EventSourceResponse,
    dependencies=[Depends(rate_limit(settings.RATE_LIMIT_PLAN, "plan"))],
    responses={
        200: {"content": {"text/event-stream": {}}, "description": "Stream of AgentEvent objects"}
    },
)
async def plan_trip(
    trip_id: uuid.UUID,
    data: PlanRequest,
    session: SessionDep,
    user: CurrentUser,
    integrations: IntegrationsDep,
    limiter: LimiterDep,
) -> EventSourceResponse:
    planner = PlanningService(session, user, integrations, limiter)
    trip = await planner.start(trip_id)

    async def events() -> AsyncIterator[ServerSentEvent]:
        async for event in planner.stream(trip, data.instructions):
            yield ServerSentEvent(data=event.model_dump_json(), event=event.kind)

    return EventSourceResponse(events(), ping=15, headers={"X-Accel-Buffering": "no"})


@router.get("/{trip_id}/itinerary", response_model=list[ItineraryItemRead])
async def list_itinerary(trip_id: uuid.UUID, service: Service) -> list[ItineraryItemRead]:
    return [ItineraryItemRead.model_validate(i) for i in await service.items(trip_id)]


@router.post(
    "/{trip_id}/itinerary", response_model=ItineraryItemRead, status_code=status.HTTP_201_CREATED
)
async def add_itinerary_item(
    trip_id: uuid.UUID, data: ItineraryItemCreate, service: Service
) -> ItineraryItemRead:
    return ItineraryItemRead.model_validate(await service.add_item(trip_id, data))


@router.patch("/{trip_id}/itinerary/{item_id}", response_model=ItineraryItemRead)
async def update_itinerary_item(
    trip_id: uuid.UUID, item_id: uuid.UUID, data: ItineraryItemUpdate, service: Service
) -> ItineraryItemRead:
    return ItineraryItemRead.model_validate(await service.update_item(trip_id, item_id, data))


@router.delete("/{trip_id}/itinerary/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_itinerary_item(trip_id: uuid.UUID, item_id: uuid.UUID, service: Service) -> None:
    await service.delete_item(trip_id, item_id)


@router.get("/{trip_id}/bookings", response_model=list[BookingRead])
async def list_bookings(trip_id: uuid.UUID, service: Service) -> list[BookingRead]:
    return [BookingRead.model_validate(b) for b in await service.bookings(trip_id)]


@router.post(
    "/{trip_id}/bookings/{booking_id}/confirm",
    response_model=BookingRead,
    summary="Confirm a quoted booking (simulated; requires the user's explicit action)",
)
async def confirm_booking(
    trip_id: uuid.UUID, booking_id: uuid.UUID, service: Service
) -> BookingRead:
    return BookingRead.model_validate(await service.confirm_booking(trip_id, booking_id))


@router.post("/{trip_id}/bookings/{booking_id}/cancel", response_model=BookingRead)
async def cancel_booking(
    trip_id: uuid.UUID, booking_id: uuid.UUID, service: Service
) -> BookingRead:
    return BookingRead.model_validate(await service.cancel_booking(trip_id, booking_id))


@router.get("/{trip_id}/photos", response_model=list[PhotoRead])
async def list_photos(trip_id: uuid.UUID, service: Service) -> list[PhotoRead]:
    return [PhotoRead.model_validate(p) for p in await service.photos(trip_id)]


@router.post(
    "/{trip_id}/photos/refresh",
    response_model=list[PhotoRead],
    dependencies=[Depends(rate_limit("10/hour", "photos"))],
)
async def refresh_photos(trip_id: uuid.UUID, service: Service) -> list[PhotoRead]:
    return [PhotoRead.model_validate(p) for p in await service.refresh_photos(trip_id)]


@router.get("/{trip_id}/weather", response_model=list[WeatherDay])
async def trip_weather(trip_id: uuid.UUID, service: Service) -> list[WeatherDay]:
    return [WeatherDay.model_validate(d.model_dump()) for d in await service.weather(trip_id)]


@router.get("/{trip_id}/map", response_model=TripMap, summary="Stops and daily routes as GeoJSON")
async def trip_map(trip_id: uuid.UUID, service: Service) -> TripMap:
    return await service.map(trip_id)
