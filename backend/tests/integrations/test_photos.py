from typing import Any

import httpx
import respx

from app.integrations.photos import FallbackPhotos
from app.integrations.photos.unsplash import UnsplashPhotos, with_utm
from app.integrations.photos.wikimedia import WikimediaPhotos, plain_text
from app.integrations.ports import Photo

UNSPLASH_SEARCH = "https://api.unsplash.com/search/photos"
COMMONS = "https://commons.wikimedia.org/w/api.php"
DOWNLOAD_LOCATION = (
    "https://api.unsplash.com/photos/Yizrl9N_eDA/download?ixid=M3w1MDk0NjZ8MHwxfHNlYXJjaHwx"
)

UNSPLASH_RESULTS: dict[str, Any] = {
    "total": 133,
    "total_pages": 67,
    "results": [
        {
            "id": "Yizrl9N_eDA",
            "created_at": "2019-02-10T08:28:02Z",
            "width": 6000,
            "height": 4000,
            "color": "#a6c0d9",
            "blur_hash": "LfHLkXof00WB~qayM{j[IUayofj[",
            "description": None,
            "alt_description": "boat on Phewa lake with mountains behind",
            "urls": {
                "raw": "https://images.unsplash.com/photo-1549880338-65ddcdfd017b?ixid=abc",
                "full": "https://images.unsplash.com/photo-1549880338-65ddcdfd017b?ixid=abc&q=85",
                "regular": "https://images.unsplash.com/photo-1549880338-65ddcdfd017b?ixid=abc&w=1080",
                "small": "https://images.unsplash.com/photo-1549880338-65ddcdfd017b?ixid=abc&w=400",
                "thumb": "https://images.unsplash.com/photo-1549880338-65ddcdfd017b?ixid=abc&w=200",
            },
            "links": {
                "self": "https://api.unsplash.com/photos/Yizrl9N_eDA",
                "html": "https://unsplash.com/photos/Yizrl9N_eDA",
                "download": "https://unsplash.com/photos/Yizrl9N_eDA/download",
                "download_location": DOWNLOAD_LOCATION,
            },
            "user": {
                "id": "u1",
                "username": "sanjaysharma",
                "name": "Sanjay Sharma",
                "links": {"html": "https://unsplash.com/@sanjaysharma"},
            },
        }
    ],
}

COMMONS_RESULTS: dict[str, Any] = {
    "batchcomplete": True,
    "query": {
        "pages": [
            {
                "pageid": 2,
                "ns": 6,
                "title": "File:Pokhara map.svg",
                "index": 2,
                "imageinfo": [
                    {
                        "size": 1000,
                        "width": 1000,
                        "height": 800,
                        "thumburl": "https://upload.wikimedia.org/thumb/map.svg/800px-map.svg.png",
                        "thumbwidth": 800,
                        "thumbheight": 640,
                        "url": "https://upload.wikimedia.org/map.svg",
                        "descriptionurl": "https://commons.wikimedia.org/wiki/File:Pokhara_map.svg",
                        "extmetadata": {},
                    }
                ],
            },
            {
                "pageid": 1,
                "ns": 6,
                "title": "File:Phewa Lake, Pokhara.jpg",
                "index": 1,
                "imageinfo": [
                    {
                        "size": 4123456,
                        "width": 4000,
                        "height": 2667,
                        "thumburl": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Phewa_Lake%2C_Pokhara.jpg/800px-Phewa_Lake%2C_Pokhara.jpg",
                        "thumbwidth": 800,
                        "thumbheight": 533,
                        "url": "https://upload.wikimedia.org/wikipedia/commons/a/ab/Phewa_Lake%2C_Pokhara.jpg",
                        "descriptionurl": "https://commons.wikimedia.org/wiki/File:Phewa_Lake,_Pokhara.jpg",
                        "descriptionshorturl": "https://commons.wikimedia.org/w/index.php?curid=1",
                        "extmetadata": {
                            "Artist": {
                                "value": '<a href="//commons.wikimedia.org/wiki/User:Krish_Dulal" title="User:Krish Dulal">Krish Dulal</a>',
                                "source": "commons-desc-page",
                            },
                            "ImageDescription": {
                                "value": "<p>Phewa Lake &amp; the Annapurna range at dawn</p>",
                                "source": "commons-desc-page",
                            },
                            "LicenseShortName": {
                                "value": "CC BY-SA 3.0",
                                "source": "commons-desc-page",
                            },
                        },
                    }
                ],
            },
            {
                "pageid": 3,
                "ns": 6,
                "title": "File:Tiny boat.jpg",
                "index": 3,
                "imageinfo": [
                    {
                        "width": 300,
                        "height": 200,
                        "url": "https://upload.wikimedia.org/tiny.jpg",
                        "descriptionurl": "https://commons.wikimedia.org/wiki/File:Tiny_boat.jpg",
                    }
                ],
            },
        ]
    },
}


def test_with_utm() -> None:
    assert (
        with_utm("https://unsplash.com/@a")
        == "https://unsplash.com/@a?utm_source=travya&utm_medium=referral"
    )
    assert (
        with_utm("https://x.org/p?id=1")
        == "https://x.org/p?id=1&utm_source=travya&utm_medium=referral"
    )


async def test_unsplash_search_follows_guidelines(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter
) -> None:
    route = respx_mock.get(UNSPLASH_SEARCH).respond(json=UNSPLASH_RESULTS)

    photos = await UnsplashPhotos(http, "unsplash-key").search("Pokhara", limit=4)

    request = route.calls.last.request
    assert request.headers["Authorization"] == "Client-ID unsplash-key"
    assert request.url.params["query"] == "Pokhara"
    assert request.url.params["orientation"] == "landscape"
    assert request.url.params["per_page"] == "4"
    [photo] = photos
    assert photo.url.endswith("&w=1080")
    assert photo.thumb_url.endswith("&w=400")
    assert (photo.width, photo.height) == (1080, 720)
    assert photo.alt == "boat on Phewa lake with mountains behind"
    assert photo.author_name == "Sanjay Sharma"
    assert (
        photo.author_url
        == "https://unsplash.com/@sanjaysharma?utm_source=travya&utm_medium=referral"
    )
    assert (
        photo.source_url
        == "https://unsplash.com/photos/Yizrl9N_eDA?utm_source=travya&utm_medium=referral"
    )
    assert photo.download_location == DOWNLOAD_LOCATION
    assert photo.source == "unsplash"


async def test_unsplash_search_is_cached(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter
) -> None:
    route = respx_mock.get(UNSPLASH_SEARCH).respond(json=UNSPLASH_RESULTS)
    unsplash = UnsplashPhotos(http, "k")
    await unsplash.search("Pokhara")
    await unsplash.search("pokhara")
    assert route.call_count == 1


async def test_unsplash_track_download_calls_download_location(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter
) -> None:
    respx_mock.get(UNSPLASH_SEARCH).respond(json=UNSPLASH_RESULTS)
    tracked = respx_mock.get(DOWNLOAD_LOCATION).respond(
        json={"url": "https://images.unsplash.com/x"}
    )
    unsplash = UnsplashPhotos(http, "unsplash-key")
    [photo] = await unsplash.search("Pokhara")

    await unsplash.track_download(photo)

    assert tracked.call_count == 1
    assert tracked.calls.last.request.headers["Authorization"] == "Client-ID unsplash-key"


async def test_unsplash_never_sends_the_key_elsewhere(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter
) -> None:
    photo = Photo(
        url="https://images.unsplash.com/x",
        thumb_url="https://images.unsplash.com/x",
        width=1080,
        height=720,
        alt="x",
        author_name="x",
        source="unsplash",
        source_url="https://unsplash.com/photos/x",
        download_location="https://attacker.example/collect",
    )
    await UnsplashPhotos(http, "k").track_download(photo)
    assert not respx_mock.calls


async def test_unsplash_track_download_failure_is_swallowed(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter, sleeps: list[float]
) -> None:
    respx_mock.get(UNSPLASH_SEARCH).respond(json=UNSPLASH_RESULTS)
    respx_mock.get(DOWNLOAD_LOCATION).respond(503)
    unsplash = UnsplashPhotos(http, "k")
    [photo] = await unsplash.search("Pokhara")
    await unsplash.track_download(photo)


async def test_wikimedia_search(http: httpx.AsyncClient, respx_mock: respx.MockRouter) -> None:
    route = respx_mock.get(COMMONS).respond(json=COMMONS_RESULTS)

    photos = await WikimediaPhotos(http).search("Pokhara", limit=3)

    params = route.calls.last.request.url.params
    assert params["generator"] == "search"
    assert params["gsrnamespace"] == "6"
    assert params["prop"] == "imageinfo"
    assert params["iiprop"] == "url|size|extmetadata"
    assert params["iiurlwidth"] == "800"
    assert params["gsrsearch"].startswith("Pokhara")
    # the SVG map and the tiny image are skipped
    [photo] = photos
    assert photo.url.endswith("/800px-Phewa_Lake%2C_Pokhara.jpg")
    assert (photo.width, photo.height) == (800, 533)
    assert photo.author_name == "Krish Dulal"
    assert photo.author_url == "https://commons.wikimedia.org/wiki/User:Krish_Dulal"
    assert photo.alt == "Phewa Lake & the Annapurna range at dawn"
    assert photo.source == "wikimedia"
    assert photo.source_url == "https://commons.wikimedia.org/wiki/File:Phewa_Lake,_Pokhara.jpg"


def test_plain_text_strips_markup() -> None:
    assert plain_text('<span class="x">Jane&nbsp;<b>Doe</b></span>\n') == "Jane Doe"


async def test_fallback_photos_uses_wikimedia_when_unsplash_fails(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter, sleeps: list[float]
) -> None:
    respx_mock.get(UNSPLASH_SEARCH).respond(403, text="Rate Limit Exceeded")
    respx_mock.get(COMMONS).respond(json=COMMONS_RESULTS)
    photos = FallbackPhotos(UnsplashPhotos(http, "k"), WikimediaPhotos(http))

    results = await photos.search("Pokhara")

    assert [p.source for p in results] == ["wikimedia"]
    calls = len(respx_mock.calls)
    await photos.track_download(results[0])
    assert len(respx_mock.calls) == calls


async def test_fallback_photos_prefers_unsplash(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter
) -> None:
    respx_mock.get(UNSPLASH_SEARCH).respond(json=UNSPLASH_RESULTS)
    commons = respx_mock.get(COMMONS).respond(json=COMMONS_RESULTS)
    results = await FallbackPhotos(UnsplashPhotos(http, "k"), WikimediaPhotos(http)).search(
        "Pokhara"
    )
    assert [p.source for p in results] == ["unsplash"]
    assert not commons.called
