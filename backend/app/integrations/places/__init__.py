"""Points of interest: OpenStreetMap via Overpass, with Wikipedia geosearch when Overpass is slow or down."""

import asyncio

from app.core.errors import UpstreamUnavailable
from app.core.logging import get_logger
from app.integrations.ports import GeoPoint, Place, PlacesSearch, PoiCategory

log = get_logger(__name__)

PRIMARY_BUDGET_S = 12.0  # the backup query runs meanwhile


class FallbackPlaces:
    """The public Overpass servers are often overloaded; never let them hold a plan for minutes."""

    def __init__(self, primary: PlacesSearch, fallback: PlacesSearch) -> None:
        self._primary = primary
        self._fallback = fallback

    async def nearby(
        self,
        center: GeoPoint,
        *,
        categories: list[PoiCategory],
        radius_m: int = 3000,
        limit: int = 30,
    ) -> list[Place]:
        backup = asyncio.create_task(
            self._fallback.nearby(center, categories=categories, radius_m=radius_m, limit=limit)
        )
        try:
            async with asyncio.timeout(PRIMARY_BUDGET_S):
                places = await self._primary.nearby(
                    center, categories=categories, radius_m=radius_m, limit=limit
                )
            if places:
                backup.cancel()
                return places
        except (UpstreamUnavailable, TimeoutError) as exc:
            log.warning("places_fallback", error=type(exc).__name__)
        except BaseException:
            backup.cancel()
            raise
        return await backup
