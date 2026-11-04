"""Photon (komoot) search-as-you-type over OpenStreetMap data."""

from typing import Any

import httpx
from cashews import cache

from app.integrations.caching import AUTOCOMPLETE_TTL, non_empty
from app.integrations.http import fetch_json
from app.integrations.ports import GeoPoint, Place

BASE_URL = "https://photon.komoot.io"
MIN_QUERY_CHARS = 2
_OSM_TYPES = {"N": "node", "W": "way", "R": "relation"}


class PhotonAutocomplete:
    def __init__(self, http: httpx.AsyncClient, base_url: str = BASE_URL) -> None:
        self._http = http
        self._base_url = base_url.rstrip("/")

    async def suggest(
        self, query: str, *, limit: int = 6, near: GeoPoint | None = None
    ) -> list[Place]:
        query = query.strip()
        if len(query) < MIN_QUERY_CHARS:
            return []
        if near is not None:
            # the bias only needs to be rough, and a coarse point keeps the cache useful
            near = GeoPoint(lat=round(near.lat, 2), lon=round(near.lon, 2))
        return await self._suggest(query, limit, near)

    @cache(
        ttl=AUTOCOMPLETE_TTL,
        key="photon:{query:lower}:{limit}:{near.lat}:{near.lon}",
        condition=non_empty,
    )
    async def _suggest(self, query: str, limit: int, near: GeoPoint | None) -> list[Place]:
        params: dict[str, Any] = {"q": query, "limit": limit, "lang": "en"}
        if near is not None:
            # zoom 10 biases towards the region rather than the street, so prominent places still win
            params |= {"lat": near.lat, "lon": near.lon, "zoom": 10}
        data = await fetch_json(self._http, "GET", f"{self._base_url}/api", params=params)
        places: dict[str, Place] = {}
        for feature in data.get("features", []):
            place = to_place(feature)
            if place is not None:
                places.setdefault(place.display_name, place)
        return list(places.values())[:limit]


def to_place(feature: dict[str, Any]) -> Place | None:
    props: dict[str, Any] = feature.get("properties") or {}
    coordinates = (feature.get("geometry") or {}).get("coordinates") or []
    street = " ".join(str(p) for p in (props.get("housenumber"), props.get("street")) if p)
    name = props.get("name") or street
    if not name or len(coordinates) != 2:
        return None
    context = [props.get(key) for key in ("city", "state", "country")]
    display_name = ", ".join(dict.fromkeys(p for p in (name, *context) if p))
    address = ", ".join(
        p for p in (street, props.get("postcode"), props.get("city"), props.get("country")) if p
    )
    osm_type = _OSM_TYPES.get(props.get("osm_type", ""))
    country_code = props.get("countrycode")
    return Place(
        name=name,
        display_name=display_name,
        lat=float(coordinates[1]),
        lon=float(coordinates[0]),
        category=props.get("type") or props.get("osm_value"),
        country_code=country_code.upper() if country_code else None,
        address=address or None,
        osm_ref=f"{osm_type}/{props['osm_id']}" if osm_type and props.get("osm_id") else None,
        source="photon",
    )
