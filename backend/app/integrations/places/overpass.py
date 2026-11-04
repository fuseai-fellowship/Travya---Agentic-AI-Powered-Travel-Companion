"""Points of interest around a point, from OpenStreetMap via the Overpass API."""

from itertools import chain, zip_longest
from typing import Any

import httpx
from cashews import cache

from app.core.errors import UpstreamUnavailable
from app.integrations.caching import PLACES_TTL, non_empty
from app.integrations.geo import haversine_m
from app.integrations.http import fetch_json
from app.integrations.ports import GeoPoint, Place, PoiCategory

BASE_URL = "https://overpass-api.de/api/interpreter"
QUERY_TIMEOUT_S = 25
MAX_RADIUS_M = 25_000

CATEGORY_TAGS: dict[PoiCategory, tuple[tuple[str, str], ...]] = {
    "attraction": (("tourism", "attraction"),),
    "museum": (("tourism", "museum"), ("tourism", "gallery")),
    "viewpoint": (("tourism", "viewpoint"),),
    "park": (("leisure", "park"), ("leisure", "garden")),
    "restaurant": (("amenity", "restaurant"),),
    "cafe": (("amenity", "cafe"),),
    "nightlife": (("amenity", "bar"), ("amenity", "pub"), ("amenity", "nightclub")),
    "shopping": (("shop", "mall"), ("shop", "department_store"), ("amenity", "marketplace")),
    "religious": (("amenity", "place_of_worship"),),
    "hotel": (("tourism", "hotel"), ("tourism", "guest_house"), ("tourism", "hostel")),
}


class OverpassPlaces:
    def __init__(self, http: httpx.AsyncClient, url: str = BASE_URL) -> None:
        self._http = http
        self._url = url

    async def nearby(
        self,
        center: GeoPoint,
        *,
        categories: list[PoiCategory],
        radius_m: int = 3000,
        limit: int = 30,
    ) -> list[Place]:
        wanted = tuple(sorted(set(categories)))
        if not wanted or limit <= 0:
            return []
        radius_m = max(1, min(radius_m, MAX_RADIUS_M))
        return await self._nearby(
            round(center.lat, 4), round(center.lon, 4), wanted, radius_m, limit
        )

    @cache(
        ttl=PLACES_TTL,
        key="overpass:{lat}:{lon}:{categories}:{radius_m}:{limit}",
        condition=non_empty,
    )
    async def _nearby(
        self, lat: float, lon: float, categories: tuple[PoiCategory, ...], radius_m: int, limit: int
    ) -> list[Place]:
        # fetch more than needed so dedupe and the wiki preference have room to choose
        query = build_query(
            lat, lon, categories, radius_m, max_elements=min(max(limit * 6, 60), 500)
        )
        data = await fetch_json(
            self._http, "POST", self._url, data={"data": query}, timeout_s=QUERY_TIMEOUT_S + 10
        )
        elements = data.get("elements") or []
        if not elements and "error" in (data.get("remark") or ""):
            raise UpstreamUnavailable(f"Overpass query failed: {data['remark'][:200]}")
        return select_places(elements, categories, GeoPoint(lat=lat, lon=lon), limit)


def build_query(
    lat: float, lon: float, categories: tuple[PoiCategory, ...], radius_m: int, *, max_elements: int
) -> str:
    values_by_key: dict[str, set[str]] = {}
    for category in categories:
        for key, value in CATEGORY_TAGS[category]:
            values_by_key.setdefault(key, set()).add(value)
    around = f"(around:{radius_m},{lat},{lon})"
    clauses = "".join(
        f'nwr["{key}"~"^({"|".join(sorted(values))})$"]["name"]{around};'
        for key, values in sorted(values_by_key.items())
    )
    # notable places are output first so the element cap never cuts them off
    return (
        f"[out:json][timeout:{QUERY_TIMEOUT_S}];({clauses})->.poi;"
        f"nwr.poi[wikidata];out center {max_elements};"
        f".poi out center {max_elements};"
    )


def select_places(
    elements: list[dict[str, Any]],
    categories: tuple[PoiCategory, ...],
    center: GeoPoint,
    limit: int,
) -> list[Place]:
    """Dedupe, prefer notable places (wikipedia/wikidata tags) and nearer ones, mix categories."""
    candidates: list[tuple[bool, float, Place]] = []
    for element in elements:
        place = _to_place(element, categories)
        if place is not None:
            notable = bool({"wikipedia", "wikidata"} & set(element.get("tags", {})))
            distance = haversine_m(center.lat, center.lon, place.lat, place.lon)
            candidates.append((not notable, distance, place))
    candidates.sort(key=lambda c: (c[0], c[1]))

    seen: set[tuple[str, float, float]] = set()
    by_category: dict[str, list[Place]] = {category: [] for category in categories}
    for _, _, place in candidates:
        identity = (place.name.casefold(), round(place.lat, 3), round(place.lon, 3))
        if identity not in seen:
            seen.add(identity)
            by_category[place.category or ""].append(place)
    mixed = chain.from_iterable(zip_longest(*by_category.values()))
    return [place for place in mixed if place is not None][:limit]


def _to_place(element: dict[str, Any], categories: tuple[PoiCategory, ...]) -> Place | None:
    tags: dict[str, str] = element.get("tags") or {}
    name = tags.get("name:en") or tags.get("name")
    point = element if "lat" in element else element.get("center")
    category = next(
        (c for c in categories if any(tags.get(k) == v for k, v in CATEGORY_TAGS[c])), None
    )
    if not name or not point or category is None:
        return None
    street = " ".join(p for p in (tags.get("addr:housenumber"), tags.get("addr:street")) if p)
    address = ", ".join(p for p in (street, tags.get("addr:city")) if p) or None
    return Place(
        name=name,
        display_name=f"{name}, {address}" if address else name,
        lat=float(point["lat"]),
        lon=float(point["lon"]),
        category=category,
        country_code=tags.get("addr:country"),
        address=address,
        opening_hours=tags.get("opening_hours"),
        website=tags.get("website") or tags.get("contact:website"),
        osm_ref=f"{element['type']}/{element['id']}",
        source="overpass",
    )
