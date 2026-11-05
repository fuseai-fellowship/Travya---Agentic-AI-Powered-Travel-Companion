"""Cache TTLs and conditions for adapter results.

Adapters use cashews decorators; the app picks the backend (`cache.setup(...)`) at startup.
"""

from datetime import timedelta
from typing import Any

GEOCODE_TTL = timedelta(days=30)
AUTOCOMPLETE_TTL = timedelta(days=1)
PLACES_TTL = timedelta(days=7)
ROUTE_TTL = timedelta(days=7)
FORECAST_TTL = timedelta(hours=3)
CLIMATE_TTL = timedelta(days=30)
GUIDE_TTL = timedelta(days=30)
PHOTOS_TTL = timedelta(days=7)


def non_empty(result: Any, args: tuple[Any, ...], kwargs: dict[str, Any], key: str = "") -> bool:
    """Store only useful results: never None or an empty list."""
    return result is not None and result != []
