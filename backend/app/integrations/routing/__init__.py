"""Routing between waypoints: OpenRouteService with a key, FOSSGIS OSRM without one."""

from app.core.errors import UpstreamUnavailable
from app.core.logging import get_logger
from app.integrations.ports import GeoPoint, Route, RouteProfile, Router

log = get_logger(__name__)

MAX_WAYPOINTS = 25

Waypoints = tuple[tuple[float, float], ...]


def prepare_waypoints(points: list[GeoPoint], source: str) -> Waypoints | None:
    """[lon, lat] pairs for the request, or None when there is nothing to route."""
    if len(points) < 2:
        return None
    if len(points) > MAX_WAYPOINTS:
        log.info(
            "route_waypoints_truncated", source=source, requested=len(points), kept=MAX_WAYPOINTS
        )
        points = [*points[: MAX_WAYPOINTS - 1], points[-1]]
    return tuple((round(p.lon, 6), round(p.lat, 6)) for p in points)


class FallbackRouter:
    """Uses the primary router and switches to the fallback while the primary is unavailable."""

    def __init__(self, primary: Router, fallback: Router) -> None:
        self._primary = primary
        self._fallback = fallback

    async def route(
        self, points: list[GeoPoint], *, profile: RouteProfile = "foot"
    ) -> Route | None:
        try:
            return await self._primary.route(points, profile=profile)
        except UpstreamUnavailable:
            log.warning("router_fallback", profile=profile)
            return await self._fallback.route(points, profile=profile)
