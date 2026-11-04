"""Destination search and guides for the trip form and the explore view."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, IntegrationsDep, rate_limit
from app.core.errors import NotFound
from app.schemas.content import GuideRead, PlaceSuggestion

router = APIRouter(prefix="/explore", tags=["explore"])


@router.get(
    "/places",
    response_model=list[PlaceSuggestion],
    summary="Autocomplete destinations (Photon / OpenStreetMap)",
    dependencies=[Depends(rate_limit("120/minute", "autocomplete"))],
)
async def suggest_places(
    _: CurrentUser,
    integrations: IntegrationsDep,
    q: Annotated[str, Query(min_length=2, max_length=100)],
    limit: Annotated[int, Query(ge=1, le=10)] = 6,
) -> list[PlaceSuggestion]:
    places = await integrations.autocomplete.suggest(q, limit=limit)
    return [PlaceSuggestion.model_validate(p.model_dump()) for p in places]


@router.get("/guide", response_model=GuideRead, summary="Destination guide (Wikivoyage, CC BY-SA)")
async def destination_guide(
    _: CurrentUser,
    integrations: IntegrationsDep,
    destination: Annotated[str, Query(min_length=2, max_length=100)],
) -> GuideRead:
    guide = await integrations.guides.guide(destination)
    if guide is None:
        raise NotFound(f"No guide found for {destination}")
    return GuideRead(
        destination=guide.destination,
        summary=guide.summary,
        sections=[s.model_dump() for s in guide.sections],
        url=guide.url,
        source=guide.source,
        license=guide.license,
    )
