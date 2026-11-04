"""Keyless routing on the FOSSGIS OSRM servers (routing.openstreetmap.de)."""

import httpx
from cashews import cache

from app.core.logging import get_logger
from app.integrations.caching import ROUTE_TTL, non_empty
from app.integrations.http import parse_json, send_with_retry
from app.integrations.ports import GeoPoint, Route, RouteProfile
from app.integrations.routing import Waypoints, prepare_waypoints

log = get_logger(__name__)

BASE_URL = "https://routing.openstreetmap.de"
PROFILES: dict[RouteProfile, str] = {
    "foot": "routed-foot",
    "car": "routed-car",
    "bike": "routed-bike",
}


class OsrmRouter:
    def __init__(self, http: httpx.AsyncClient, base_url: str = BASE_URL) -> None:
        self._http = http
        self._base_url = base_url.rstrip("/")

    async def route(
        self, points: list[GeoPoint], *, profile: RouteProfile = "foot"
    ) -> Route | None:
        waypoints = prepare_waypoints(points, "osrm")
        return await self._route(profile, waypoints) if waypoints else None

    @cache(ttl=ROUTE_TTL, key="osrm:{profile}:{waypoints:hash}", condition=non_empty)
    async def _route(self, profile: RouteProfile, waypoints: Waypoints) -> Route | None:
        path = ";".join(f"{lon:.6f},{lat:.6f}" for lon, lat in waypoints)
        url = f"{self._base_url}/{PROFILES[profile]}/route/v1/driving/{path}"
        response = await send_with_retry(
            self._http, "GET", url, params={"overview": "full", "geometries": "geojson"}
        )
        if response.status_code == 400:
            # OSRM answers 400 with a code such as NoSegment when a point is not routable
            log.info("osrm_no_route", profile=profile, body=response.text[:200])
            return None
        data = parse_json(response)
        if data.get("code") != "Ok" or not data.get("routes"):
            log.info("osrm_no_route", profile=profile, code=data.get("code"))
            return None
        best = data["routes"][0]
        return Route(
            profile=profile,
            distance_m=float(best["distance"]),
            duration_s=float(best["duration"]),
            geometry=[(float(c[0]), float(c[1])) for c in best["geometry"]["coordinates"]],
            source="osrm",
        )
