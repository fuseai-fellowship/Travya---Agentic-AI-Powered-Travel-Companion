"""Nominatim (OpenStreetMap) search and reverse geocoding.

Usage policy: at most one request per second (see `http.HOST_RATE_LIMITS`), an identifying
User-Agent, cached results and no autocomplete (Photon handles that).
"""

from typing import Any

import httpx
from cashews import cache

from app.integrations.caching import GEOCODE_TTL, non_empty
from app.integrations.http import fetch_json
from app.integrations.ports import GeoPoint, Place

BASE_URL = "https://nominatim.openstreetmap.org"
_COMMON_PARAMS = {"format": "jsonv2", "addressdetails": 1, "accept-language": "en"}


class NominatimGeocoder:
    def __init__(self, http: httpx.AsyncClient, base_url: str = BASE_URL) -> None:
        self._http = http
        self._base_url = base_url.rstrip("/")

    @cache(ttl=GEOCODE_TTL, key="nominatim:search:{query:lower}:{limit}", condition=non_empty)
    async def search(self, query: str, *, limit: int = 5) -> list[Place]:
        if not query.strip():
            return []
        params = {**_COMMON_PARAMS, "q": query.strip(), "limit": limit}
        data = await fetch_json(self._http, "GET", f"{self._base_url}/search", params=params)
        return [to_place(item) for item in data]

    @cache(ttl=GEOCODE_TTL, key="nominatim:reverse:{point.lat}:{point.lon}", condition=non_empty)
    async def reverse(self, point: GeoPoint) -> Place | None:
        params = {**_COMMON_PARAMS, "lat": point.lat, "lon": point.lon}
        data = await fetch_json(self._http, "GET", f"{self._base_url}/reverse", params=params)
        if not isinstance(data, dict) or "error" in data:
            return None
        return to_place(data)


def to_place(item: dict[str, Any]) -> Place:
    address: dict[str, str] = item.get("address") or {}
    display_name: str = item.get("display_name") or ""
    country_code = address.get("country_code")
    osm_type, osm_id = item.get("osm_type"), item.get("osm_id")
    return Place(
        name=item.get("name") or display_name.split(",")[0],
        display_name=display_name,
        lat=float(item["lat"]),
        lon=float(item["lon"]),
        category=item.get("addresstype") or item.get("type"),
        country_code=country_code.upper() if country_code else None,
        address=_format_address(address),
        osm_ref=f"{osm_type}/{osm_id}" if osm_type and osm_id else None,
        source="nominatim",
    )


def _format_address(address: dict[str, str]) -> str | None:
    street = " ".join(part for part in (address.get("house_number"), address.get("road")) if part)
    locality = next(
        (address[key] for key in ("city", "town", "village", "hamlet") if address.get(key)), None
    )
    parts = (
        street,
        address.get("suburb"),
        locality,
        address.get("postcode"),
        address.get("country"),
    )
    return ", ".join(part for part in parts if part) or None
