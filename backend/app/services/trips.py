"""Trips, itinerary, simulated bookings, photos, weather and the trip map."""

import math
import secrets
import uuid
from collections import defaultdict
from datetime import UTC, date, datetime
from typing import Any

from sqlmodel import col
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.errors import Conflict, InvalidInput
from app.core.logging import get_logger
from app.integrations.ports import DailyWeather, GeoPoint
from app.integrations.registry import Integrations
from app.models import (
    Booking,
    BookingStatus,
    ItineraryItem,
    Trip,
    TripPhoto,
    TripStatus,
    User,
)
from app.repositories import (
    BookingRepository,
    ItineraryRepository,
    PhotoRepository,
    TripRepository,
    newest_first,
)
from app.schemas.maps import Feature, TripMap
from app.schemas.trips import (
    ItineraryItemCreate,
    ItineraryItemUpdate,
    TripCreate,
    TripUpdate,
)
from app.services.documents import DocumentService

log = get_logger(__name__)

WALKABLE_KM = 6.0


def _km(a: GeoPoint, b: GeoPoint) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (a.lat, a.lon, b.lat, b.lon))
    h = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    return 6371 * 2 * math.asin(math.sqrt(h))


class TripService:
    def __init__(self, session: AsyncSession, user: User, integrations: Integrations) -> None:
        self.session = session
        self.user = user
        self.integrations = integrations
        self.trips = TripRepository(session, user.id)

    # Trips

    async def create(self, data: TripCreate) -> Trip:
        trip = Trip(owner_id=self.user.id, **data.model_dump())
        matches = await self.integrations.geocoder.search(data.destination, limit=1)
        if matches:
            place = matches[0]
            trip.latitude, trip.longitude = place.lat, place.lon
            trip.country_code = (place.country_code or "").upper()[:2] or None
        try:
            photos = await self.integrations.photos.search(data.destination, limit=1)
        except Exception as exc:  # a cover photo is decoration; never block trip creation
            log.warning("cover_photo_failed", error=str(exc))
            photos = []
        if photos:
            trip.cover_photo_url = photos[0].url
        trip = await self.trips.add(trip)
        await self.session.commit()
        return trip

    async def page(
        self, *, status: TripStatus | None, query: str | None, limit: int, offset: int
    ) -> tuple[list[Trip], int]:
        where = []
        if status:
            where.append(col(Trip.status) == status)
        if query:
            pattern = f"%{query.strip()}%"
            where.append(col(Trip.title).ilike(pattern) | col(Trip.destination).ilike(pattern))
        return await self.trips.page(
            *where,
            order_by=[col(Trip.start_date).desc(), newest_first(Trip)],
            limit=limit,
            offset=offset,
        )

    async def get(self, trip_id: uuid.UUID) -> Trip:
        return await self.trips.get(trip_id)

    async def update(self, trip_id: uuid.UUID, data: TripUpdate) -> Trip:
        trip = await self.trips.get(trip_id)
        changes = data.model_dump(exclude_unset=True)
        start = changes.get("start_date", trip.start_date)
        end = changes.get("end_date", trip.end_date)
        if end < start:
            raise InvalidInput("end_date must be on or after start_date")
        trip = await self.trips.update(trip, changes)
        await self.session.commit()
        return trip

    async def delete(self, trip_id: uuid.UUID) -> None:
        trip = await self.trips.get(trip_id)
        await DocumentService(self.session, self.user, self.integrations.storage).delete_for_trip(
            trip.id
        )
        await self.trips.delete(trip)
        await self.session.commit()

    # Itinerary

    async def items(self, trip_id: uuid.UUID) -> list[ItineraryItem]:
        trip = await self.trips.get(trip_id)
        return await ItineraryRepository(self.session, trip.id).all(
            order_by=[
                col(ItineraryItem.day),
                col(ItineraryItem.position),
                col(ItineraryItem.start_time),
            ]
        )

    def _check_day(self, trip: Trip, day: date) -> None:
        if not trip.start_date <= day <= trip.end_date:
            raise InvalidInput("The item's day must be within the trip dates")

    async def add_item(self, trip_id: uuid.UUID, data: ItineraryItemCreate) -> ItineraryItem:
        trip = await self.trips.get(trip_id)
        self._check_day(trip, data.day)
        repo = ItineraryRepository(self.session, trip.id)
        position = data.position
        if position is None:
            same_day = await repo.all(col(ItineraryItem.day) == data.day)
            position = max((i.position for i in same_day), default=-1) + 1
        item = await repo.add(
            ItineraryItem(
                trip_id=trip.id,
                source="user",
                **data.model_dump(exclude={"position"}),
                position=position,
            )
        )
        await self.session.commit()
        return item

    async def update_item(
        self, trip_id: uuid.UUID, item_id: uuid.UUID, data: ItineraryItemUpdate
    ) -> ItineraryItem:
        trip = await self.trips.get(trip_id)
        repo = ItineraryRepository(self.session, trip.id)
        item = await repo.get(item_id)
        changes = data.model_dump(exclude_unset=True)
        if "day" in changes:
            self._check_day(trip, changes["day"])
        item = await repo.update(item, changes)
        await self.session.commit()
        return item

    async def delete_item(self, trip_id: uuid.UUID, item_id: uuid.UUID) -> None:
        trip = await self.trips.get(trip_id)
        repo = ItineraryRepository(self.session, trip.id)
        await repo.delete(await repo.get(item_id))
        await self.session.commit()

    # Simulated bookings (human-in-the-loop)

    async def bookings(self, trip_id: uuid.UUID) -> list[Booking]:
        trip = await self.trips.get(trip_id)
        return await BookingRepository(self.session, trip.id).all(
            order_by=[col(Booking.kind), col(Booking.amount)]
        )

    async def confirm_booking(self, trip_id: uuid.UUID, booking_id: uuid.UUID) -> Booking:
        trip = await self.trips.get(trip_id)
        repo = BookingRepository(self.session, trip.id)
        booking = await repo.get(booking_id)
        if booking.status != BookingStatus.quoted:
            raise Conflict(f"This booking is already {booking.status.value}")
        for other in await repo.all(
            col(Booking.kind) == booking.kind, col(Booking.id) != booking.id
        ):
            if other.status == BookingStatus.quoted:
                other.status = BookingStatus.cancelled
                self.session.add(other)
        booking = await repo.update(
            booking,
            {
                "status": BookingStatus.confirmed,
                "confirmation_code": f"SIM-{secrets.token_hex(3).upper()}",
                "confirmed_at": datetime.now(UTC),
            },
        )
        if trip.status in (TripStatus.draft, TripStatus.planning, TripStatus.planned):
            await self.trips.update(trip, {"status": TripStatus.booked})
        await self.session.commit()
        return booking

    async def cancel_booking(self, trip_id: uuid.UUID, booking_id: uuid.UUID) -> Booking:
        trip = await self.trips.get(trip_id)
        repo = BookingRepository(self.session, trip.id)
        booking = await repo.get(booking_id)
        if booking.status == BookingStatus.cancelled:
            raise Conflict("This booking is already cancelled")
        booking = await repo.update(booking, {"status": BookingStatus.cancelled})
        await self.session.commit()
        return booking

    # Photos

    async def photos(self, trip_id: uuid.UUID) -> list[TripPhoto]:
        trip = await self.trips.get(trip_id)
        return await PhotoRepository(self.session, trip.id).all(order_by=[col(TripPhoto.position)])

    async def refresh_photos(self, trip_id: uuid.UUID) -> list[TripPhoto]:
        trip = await self.trips.get(trip_id)
        items = await ItineraryRepository(self.session, trip.id).all(
            col(ItineraryItem.category).in_(["sight", "activity"]),
            order_by=[col(ItineraryItem.day)],
        )
        queries = [
            trip.destination,
            *list(
                dict.fromkeys(f"{i.place_name}, {trip.destination}" for i in items if i.place_name)
            ),
        ]
        repo = PhotoRepository(self.session, trip.id)
        await repo.delete_where()
        position = 0
        seen: set[str] = set()
        for query in queries[:7]:
            for photo in await self.integrations.photos.search(
                query, limit=3 if position == 0 else 2
            ):
                if photo.url in seen:
                    continue
                seen.add(photo.url)
                await repo.add(
                    TripPhoto(
                        trip_id=trip.id,
                        place_name=query.split(",")[0],
                        position=position,
                        **photo.model_dump(exclude={"download_location"}),
                    )
                )
                position += 1
        await self.session.commit()
        return await repo.all(order_by=[col(TripPhoto.position)])

    # Weather and map

    async def weather(self, trip_id: uuid.UUID) -> list[DailyWeather]:
        trip = await self.trips.get(trip_id)
        if trip.latitude is None or trip.longitude is None:
            return []
        return await self.integrations.weather.daily(
            GeoPoint(lat=trip.latitude, lon=trip.longitude), trip.start_date, trip.end_date
        )

    async def map(self, trip_id: uuid.UUID) -> TripMap:
        trip = await self.trips.get(trip_id)
        items = await ItineraryRepository(self.session, trip.id).all(
            order_by=[col(ItineraryItem.day), col(ItineraryItem.position)]
        )
        features: list[Feature] = []
        by_day: dict[date, list[ItineraryItem]] = defaultdict(list)
        for item in items:
            if item.latitude is None or item.longitude is None:
                continue
            by_day[item.day].append(item)
            features.append(
                Feature(
                    geometry={"type": "Point", "coordinates": [item.longitude, item.latitude]},
                    properties={
                        "kind": "stop",
                        "item_id": str(item.id),
                        "title": item.title,
                        "place_name": item.place_name,
                        "category": item.category.value,
                        "day": item.day.isoformat(),
                        "day_index": (item.day - trip.start_date).days + 1,
                        "start_time": item.start_time.isoformat(timespec="minutes")
                        if item.start_time
                        else None,
                    },
                )
            )
        for day, stops in by_day.items():
            if len(stops) < 2:
                continue
            points = [GeoPoint(lat=s.latitude, lon=s.longitude) for s in stops]
            spread = max(_km(points[0], p) for p in points)
            try:
                route = await self.integrations.router.route(
                    points, profile="foot" if spread <= WALKABLE_KM else "car"
                )
            except Exception as exc:  # the map still shows stops without a route line
                log.warning("route_failed", day=day.isoformat(), error=str(exc))
                route = None
            if route:
                features.append(
                    Feature(
                        geometry={
                            "type": "LineString",
                            "coordinates": [list(p) for p in route.geometry],
                        },
                        properties={
                            "kind": "route",
                            "day": day.isoformat(),
                            "day_index": (day - trip.start_date).days + 1,
                            "profile": route.profile,
                            "distance_m": round(route.distance_m),
                            "duration_s": round(route.duration_s),
                        },
                    )
                )
        lons = [f.geometry["coordinates"][0] for f in features if f.geometry["type"] == "Point"]
        lats = [f.geometry["coordinates"][1] for f in features if f.geometry["type"] == "Point"]
        center = (
            (trip.longitude, trip.latitude)
            if trip.longitude is not None and trip.latitude is not None
            else None
        )
        bbox = (min(lons), min(lats), max(lons), max(lats)) if lons else None
        return TripMap(trip_id=trip.id, center=center, bbox=bbox, features=features)

    async def replace_agent_output(
        self, trip: Trip, items: list[ItineraryItem], quotes: list[Booking], plan: dict[str, Any]
    ) -> None:
        """Persist a fresh plan: agent items and open quotes are replaced; user items and confirmed bookings stay."""
        itinerary = ItineraryRepository(self.session, trip.id)
        await itinerary.delete_where(col(ItineraryItem.source) == "agent")
        bookings = BookingRepository(self.session, trip.id)
        await bookings.delete_where(col(Booking.status) == BookingStatus.quoted)
        for item in items:
            await itinerary.add(item)
        for quote in quotes:
            await bookings.add(quote)
        confirmed = await bookings.all(col(Booking.status) == BookingStatus.confirmed)
        await self.trips.update(
            trip,
            {
                "plan": plan,
                "planned_at": datetime.now(UTC),
                "status": TripStatus.booked if confirmed else TripStatus.planned,
            },
        )
        await self.session.commit()
