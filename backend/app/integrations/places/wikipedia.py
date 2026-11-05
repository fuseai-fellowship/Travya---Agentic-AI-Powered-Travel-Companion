"""Notable places near a point from Wikipedia's geosearch (fast, keyless fallback for Overpass)."""

import httpx
from cashews import cache

from app.integrations.caching import PLACES_TTL, non_empty
from app.integrations.http import fetch_json
from app.integrations.ports import GeoPoint, Place, PoiCategory

API_URL = "https://en.wikipedia.org/w/api.php"
MAX_RADIUS_M = 10_000  # API limit
# Articles about areas rather than places to visit
SKIP_WORDS = ("district", "municipality", "province", "constituency", "ward", "airport", "railway")


class WikipediaPlaces:
    """Only knows landmarks with articles, so every result is categorised as an attraction."""

    def __init__(self, http: httpx.AsyncClient) -> None:
        self._http = http

    async def nearby(
        self,
        center: GeoPoint,
        *,
        categories: list[PoiCategory],
        radius_m: int = 3000,
        limit: int = 30,
    ) -> list[Place]:
        sightseeing = {"attraction", "museum", "viewpoint", "park", "religious"}
        if not sightseeing.intersection(categories) or limit <= 0:
            return []
        return await self._nearby(
            round(center.lat, 4), round(center.lon, 4), min(radius_m * 2, MAX_RADIUS_M), limit
        )

    @cache(ttl=PLACES_TTL, key="wikigeo:{lat}:{lon}:{radius_m}:{limit}", condition=non_empty)
    async def _nearby(self, lat: float, lon: float, radius_m: int, limit: int) -> list[Place]:
        data = await fetch_json(
            self._http,
            "GET",
            API_URL,
            params={
                "action": "query",
                "list": "geosearch",
                "gscoord": f"{lat}|{lon}",
                "gsradius": radius_m,
                "gslimit": min(limit * 2, 100),
                "format": "json",
            },
        )
        places = []
        for item in (data.get("query") or {}).get("geosearch") or []:
            title = str(item.get("title", ""))
            if not title or any(word in title.lower() for word in SKIP_WORDS):
                continue
            places.append(
                Place(
                    name=title,
                    display_name=title,
                    lat=float(item["lat"]),
                    lon=float(item["lon"]),
                    category="attraction",
                    website=f"https://en.wikipedia.org/?curid={item['pageid']}",
                    source="wikipedia",
                )
            )
        return places[:limit]
