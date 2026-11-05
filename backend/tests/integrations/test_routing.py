import json
from typing import Any

import httpx
import pytest
import respx

from app.core.errors import UpstreamUnavailable
from app.integrations.ports import GeoPoint, Route, RouteProfile
from app.integrations.routing import MAX_WAYPOINTS, FallbackRouter, prepare_waypoints
from app.integrations.routing.ors import OrsRouter
from app.integrations.routing.osrm import OsrmRouter

THAMEL = GeoPoint(lat=27.7154, lon=85.3123)
DURBAR_SQUARE = GeoPoint(lat=27.7045, lon=85.3076)
GEOMETRY = [[85.3123, 27.7154], [85.3101, 27.7102], [85.3076, 27.7045]]

OSRM_OK: dict[str, Any] = {
    "code": "Ok",
    "routes": [
        {
            "geometry": {"type": "LineString", "coordinates": GEOMETRY},
            "legs": [
                {
                    "steps": [],
                    "summary": "",
                    "weight": 1050.2,
                    "duration": 1050.2,
                    "distance": 1458.1,
                }
            ],
            "weight_name": "duration",
            "weight": 1050.2,
            "duration": 1050.2,
            "distance": 1458.1,
        }
    ],
    "waypoints": [
        {"hint": "abc", "distance": 3.1, "name": "Thamel Marg", "location": [85.3123, 27.7154]},
        {"hint": "def", "distance": 1.2, "name": "", "location": [85.3076, 27.7045]},
    ],
}

ORS_OK: dict[str, Any] = {
    "type": "FeatureCollection",
    "bbox": [85.3076, 27.7045, 85.3123, 27.7154],
    "features": [
        {
            "bbox": [85.3076, 27.7045, 85.3123, 27.7154],
            "type": "Feature",
            "properties": {
                "segments": [{"distance": 1461.3, "duration": 1052.1, "steps": []}],
                "summary": {"distance": 1461.3, "duration": 1052.1},
                "way_points": [0, 2],
            },
            "geometry": {"coordinates": GEOMETRY, "type": "LineString"},
        }
    ],
    "metadata": {
        "attribution": "openrouteservice.org | OpenStreetMap contributors",
        "service": "routing",
    },
}

OSRM_URL = "https://routing.openstreetmap.de/routed-foot/route/v1/driving/85.312300,27.715400;85.307600,27.704500"
ORS_URL = "https://api.openrouteservice.org/v2/directions/foot-walking/geojson"


async def test_osrm_route(http: httpx.AsyncClient, respx_mock: respx.MockRouter) -> None:
    route = respx_mock.get(OSRM_URL).respond(json=OSRM_OK)

    result = await OsrmRouter(http).route([THAMEL, DURBAR_SQUARE])

    params = route.calls.last.request.url.params
    assert (params["overview"], params["geometries"]) == ("full", "geojson")
    assert result == Route(
        profile="foot",
        distance_m=1458.1,
        duration_s=1050.2,
        geometry=[(85.3123, 27.7154), (85.3101, 27.7102), (85.3076, 27.7045)],
        source="osrm",
    )


@pytest.mark.parametrize(("profile", "server"), [("car", "routed-car"), ("bike", "routed-bike")])
async def test_osrm_profiles(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter, profile: RouteProfile, server: str
) -> None:
    route = respx_mock.get(url__startswith=f"https://routing.openstreetmap.de/{server}/").respond(
        json=OSRM_OK
    )
    result = await OsrmRouter(http).route([THAMEL, DURBAR_SQUARE], profile=profile)
    assert route.called
    assert result is not None
    assert result.profile == profile


async def test_osrm_no_route_is_none_and_not_cached(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter
) -> None:
    route = respx_mock.get(OSRM_URL).mock(
        side_effect=[
            httpx.Response(
                400, json={"code": "NoSegment", "message": "Could not find a matching segment"}
            ),
            httpx.Response(200, json={"code": "NoRoute", "message": "Impossible route"}),
        ]
    )
    router = OsrmRouter(http)
    assert await router.route([THAMEL, DURBAR_SQUARE]) is None
    assert await router.route([THAMEL, DURBAR_SQUARE]) is None
    assert route.call_count == 2


async def test_osrm_is_cached(http: httpx.AsyncClient, respx_mock: respx.MockRouter) -> None:
    route = respx_mock.get(OSRM_URL).respond(json=OSRM_OK)
    router = OsrmRouter(http)
    await router.route([THAMEL, DURBAR_SQUARE])
    await router.route([THAMEL, DURBAR_SQUARE])
    assert route.call_count == 1


async def test_single_point_is_not_routed(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter
) -> None:
    assert await OsrmRouter(http).route([THAMEL]) is None
    assert not respx_mock.calls


async def test_ors_route_sends_key_and_coordinates(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter
) -> None:
    route = respx_mock.post(ORS_URL).respond(json=ORS_OK)

    result = await OrsRouter(http, "ors-test-key").route([THAMEL, DURBAR_SQUARE])

    request = route.calls.last.request
    assert request.headers["Authorization"] == "ors-test-key"
    assert json.loads(request.content) == {"coordinates": [[85.3123, 27.7154], [85.3076, 27.7045]]}
    assert result is not None
    assert (result.distance_m, result.duration_s) == (1461.3, 1052.1)
    assert result.geometry[0] == (85.3123, 27.7154)
    assert result.source == "openrouteservice"


async def test_ors_unroutable_is_none(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter
) -> None:
    respx_mock.post(ORS_URL).respond(
        404, json={"error": {"code": 2010, "message": "Could not find routable point"}}
    )
    assert await OrsRouter(http, "k").route([THAMEL, DURBAR_SQUARE]) is None


async def test_ors_bad_key_is_upstream_unavailable(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter
) -> None:
    respx_mock.post(ORS_URL).respond(403, json={"error": "Access to this API has been disallowed"})
    with pytest.raises(UpstreamUnavailable):
        await OrsRouter(http, "bad").route([THAMEL, DURBAR_SQUARE])


def test_waypoints_are_truncated_keeping_the_destination() -> None:
    points = [GeoPoint(lat=27.7 + i / 1000, lon=85.3) for i in range(30)]
    waypoints = prepare_waypoints(points, "test")
    assert waypoints is not None
    assert len(waypoints) == MAX_WAYPOINTS
    assert waypoints[-1] == (85.3, points[-1].lat)
    assert waypoints[0] == (85.3, 27.7)


async def test_fallback_router_switches_when_primary_is_down(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter, sleeps: list[float]
) -> None:
    respx_mock.post(ORS_URL).respond(503)
    respx_mock.get(OSRM_URL).respond(json=OSRM_OK)
    router = FallbackRouter(OrsRouter(http, "k"), OsrmRouter(http))

    result = await router.route([THAMEL, DURBAR_SQUARE])

    assert result is not None
    assert result.source == "osrm"
