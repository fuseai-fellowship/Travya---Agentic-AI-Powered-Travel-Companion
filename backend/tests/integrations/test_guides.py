from typing import Any

import httpx
import respx

from app.integrations.guides.wikivoyage import (
    SECTION_CHARS,
    WikivoyageGuides,
    page_title,
    parse_extract,
    trim,
)

WIKIVOYAGE = "https://en.wikivoyage.org/w/api.php"
WIKIPEDIA_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/"

LONG_SEE = " ".join(f"Sight number {i} is worth an hour of your time." for i in range(80))
POKHARA_EXTRACT = f"""Pokhara is a city in central Nepal and the gateway to the Annapurna range.

It sits on the shore of Phewa Lake and is the country's adventure capital.

Its lakeside district has cafes, bookshops and trekking outfitters.


== Understand ==
Pokhara grew as a trading post between India and Tibet.

=== Climate ===
The monsoon runs from June to September.


== Get in ==
Tourist buses run daily from Kathmandu.


== Get around ==
Walk or cycle around Lakeside; taxis are cheap.


== See ==
{LONG_SEE}


== Do ==



== Buy ==
Pashmina shawls are sold everywhere.


== Stay safe ==
Do not trek alone.
"""

POKHARA_RESPONSE: dict[str, Any] = {
    "batchcomplete": True,
    "query": {
        "normalized": [{"fromencoded": False, "from": "pokhara", "to": "Pokhara"}],
        "pages": [{"pageid": 9817, "ns": 0, "title": "Pokhara", "extract": POKHARA_EXTRACT}],
    },
}

MISSING_RESPONSE: dict[str, Any] = {
    "batchcomplete": True,
    "query": {"pages": [{"ns": 0, "title": "Bhaktapur Durbar Square", "missing": True}]},
}

WIKIPEDIA_DURBAR: dict[str, Any] = {
    "type": "standard",
    "title": "Bhaktapur Durbar Square",
    "displaytitle": "Bhaktapur Durbar Square",
    "extract": "Bhaktapur Durbar Square is the plaza in front of the royal palace of the old Bhaktapur Kingdom.",
    "content_urls": {
        "desktop": {"page": "https://en.wikipedia.org/wiki/Bhaktapur_Durbar_Square"},
        "mobile": {"page": "https://en.m.wikipedia.org/wiki/Bhaktapur_Durbar_Square"},
    },
}


def test_parse_extract_keeps_useful_sections() -> None:
    summary, sections = parse_extract(POKHARA_EXTRACT)

    assert summary.startswith("Pokhara is a city in central Nepal")
    assert "adventure capital" in summary
    assert "lakeside district" not in summary
    assert [s.title for s in sections] == ["Understand", "Get around", "See", "Stay safe"]
    understand = sections[0].text
    assert "Climate\nThe monsoon runs" in understand
    assert "==" not in understand
    see = sections[2].text
    assert len(see) <= SECTION_CHARS + 2
    assert see.endswith(". …")


def test_trim_prefers_sentence_ends() -> None:
    assert trim("Short.", 100) == "Short."
    assert trim("One sentence here. Another one that is long", 26) == "One sentence here. …"


def test_page_title_capitalises_lowercase_input() -> None:
    assert page_title("  new   york city ") == "New York City"
    assert page_title("Côte d'Azur") == "Côte d'Azur"


async def test_wikivoyage_guide(http: httpx.AsyncClient, respx_mock: respx.MockRouter) -> None:
    route = respx_mock.get(WIKIVOYAGE).respond(json=POKHARA_RESPONSE)

    guide = await WikivoyageGuides(http).guide("pokhara")

    params = route.calls.last.request.url.params
    assert params["action"] == "query"
    assert "extracts" in params["prop"]
    assert (params["explaintext"], params["redirects"], params["format"]) == ("1", "1", "json")
    assert params["titles"] == "Pokhara"
    assert guide is not None
    assert guide.destination == "Pokhara"
    assert guide.url == "https://en.wikivoyage.org/wiki/Pokhara"
    assert guide.source == "wikivoyage"
    assert guide.license == "CC BY-SA 4.0"
    assert len(guide.sections) == 4


async def test_falls_back_to_wikipedia_summary(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter
) -> None:
    respx_mock.get(WIKIVOYAGE).respond(json=MISSING_RESPONSE)
    route = respx_mock.get(WIKIPEDIA_SUMMARY + "Bhaktapur_Durbar_Square").respond(
        json=WIKIPEDIA_DURBAR
    )

    guide = await WikivoyageGuides(http).guide("Bhaktapur Durbar Square")

    assert route.called
    assert guide is not None
    assert guide.source == "wikipedia"
    assert guide.sections == []
    assert guide.summary.startswith("Bhaktapur Durbar Square is the plaza")
    assert guide.url == "https://en.wikipedia.org/wiki/Bhaktapur_Durbar_Square"


async def test_disambiguation_pages_are_not_guides(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter
) -> None:
    respx_mock.get(WIKIVOYAGE).respond(
        json={
            "query": {
                "pages": [
                    {
                        "pageid": 1,
                        "ns": 0,
                        "title": "Springfield",
                        "extract": "Springfield may refer to several places.",
                        "pageprops": {"disambiguation": ""},
                    }
                ]
            }
        }
    )
    respx_mock.get(WIKIPEDIA_SUMMARY + "Springfield").respond(
        json={
            "type": "disambiguation",
            "title": "Springfield",
            "extract": "Springfield may refer to:",
        }
    )
    assert await WikivoyageGuides(http).guide("Springfield") is None


async def test_unknown_destination_is_none_and_not_cached(
    http: httpx.AsyncClient, respx_mock: respx.MockRouter
) -> None:
    voyage = respx_mock.get(WIKIVOYAGE).respond(json=MISSING_RESPONSE)
    respx_mock.get(url__startswith=WIKIPEDIA_SUMMARY).respond(
        404,
        json={
            "type": "https://mediawiki.org/wiki/HyperSwitch/errors/not_found",
            "title": "Not found.",
        },
    )
    guides = WikivoyageGuides(http)
    assert await guides.guide("Nowhereville") is None
    assert await guides.guide("Nowhereville") is None
    assert voyage.call_count == 2


async def test_guides_are_cached(http: httpx.AsyncClient, respx_mock: respx.MockRouter) -> None:
    route = respx_mock.get(WIKIVOYAGE).respond(json=POKHARA_RESPONSE)
    guides = WikivoyageGuides(http)
    await guides.guide("Pokhara")
    await guides.guide("pokhara")
    assert route.call_count == 1
