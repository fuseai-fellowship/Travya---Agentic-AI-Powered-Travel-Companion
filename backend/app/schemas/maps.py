"""GeoJSON for a trip map: one FeatureCollection with stop points and per-day route lines."""

import uuid
from typing import Any, Literal

from app.schemas.common import ApiModel


class Feature(ApiModel):
    type: Literal["Feature"] = "Feature"
    geometry: dict[str, Any]
    properties: dict[str, Any]


class TripMap(ApiModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    trip_id: uuid.UUID
    center: tuple[float, float] | None  # [lon, lat]
    bbox: tuple[float, float, float, float] | None  # [west, south, east, north]
    features: list[Feature]
    attribution: str = "© OpenStreetMap contributors"
