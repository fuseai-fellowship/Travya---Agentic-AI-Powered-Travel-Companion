"""OpenRouteService directions (GeoJSON), used when ORS_API_KEY is set."""

import httpx
from cashews import cache

from app.core.logging import get_logger
from app.integrations.caching import ROUTE_TTL, non_empty
from app.integrations.http import parse_json, send_with_retry
from app.integrations.ports import GeoPoint, Route, RouteProfile
from app.integrations.routing import Waypoints, prepare_waypoints

log = get_logger(__name__)

BASE_URL = "https://api.openrouteservice.org"
PROFILES: dict[RouteProfile, str] = {
    "foot": "foot-walking",
    "car": "driving-car",
    "bike": "cycling-regular",
}


class OrsRouter:
    def __init__(self, http: httpx.AsyncClient, api_key: str, base_url: str = BASE_URL) -> None:
        self._http = http
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")

    async def route(
        self, points: list[GeoPoint], *, profile: RouteProfile = "foot"
    ) -> Route | None:
        waypoints = prepare_waypoints(points, "openrouteservice")
        return await self._route(profile, waypoints) if waypoints else None

    @cache(ttl=ROUTE_TTL, key="ors:{profile}:{waypoints:hash}", condition=non_empty)
    async def _route(self, profile: RouteProfile, waypoints: Waypoints) -> Route | None:
        response = await send_with_retry(
            self._http,
            "POST",
            f"{self._base_url}/v2/directions/{PROFILES[profile]}/geojson",
            json={"coordinates": [list(waypoint) for waypoint in waypoints]},
            headers={"Authorization": self._api_key, "Accept": "application/geo+json"},
        )
        if response.status_code in (400, 404):
            # unroutable points or a route over the distance limit
            log.info("ors_no_route", profile=profile, body=response.text[:200])
            return None
        features = parse_json(response).get("features") or []
        if not features:
            return None
        summary = features[0].get("properties", {}).get("summary", {})
        return Route(
            profile=profile,
            distance_m=float(summary.get("distance", 0.0)),
            duration_s=float(summary.get("duration", 0.0)),
            geometry=[(float(c[0]), float(c[1])) for c in features[0]["geometry"]["coordinates"]],
            source="openrouteservice",
        )
