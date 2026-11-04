from datetime import date
from decimal import Decimal

from app.integrations.offers.sample import SampleOffers
from app.integrations.ports import TravelOffer

DEPART = date(2027, 3, 10)
RETURN = date(2027, 3, 17)


async def _lisbon_round_trip() -> list[TravelOffer]:
    return await SampleOffers().flights(
        origin="Kathmandu",
        destination="Lisbon",
        depart=DEPART,
        return_date=RETURN,
        travelers=2,
        currency="eur",
    )


async def test_flights_are_stable_labelled_samples() -> None:
    first = await _lisbon_round_trip()
    again = await _lisbon_round_trip()

    assert first == again
    assert len(first) == 3
    assert all(o.is_sample and o.kind == "flight" for o in first)
    assert all(o.provider.startswith("Sample ") for o in first)
    assert all(o.currency == "EUR" for o in first)
    assert all(o.amount == o.amount.quantize(Decimal("0.01")) for o in first)
    assert [o.amount for o in first] == sorted(o.amount for o in first)
    for offer in first:
        per_traveler = Decimal(offer.details["price_per_traveler"])
        assert offer.amount == per_traveler * 2
        assert offer.details["return_date"] == "2027-03-17"


async def test_flights_differ_by_destination_and_currency() -> None:
    offers = SampleOffers()
    lisbon = await offers.flights(
        origin=None,
        destination="Lisbon",
        depart=DEPART,
        return_date=None,
        travelers=1,
        currency="USD",
    )
    tokyo = await offers.flights(
        origin=None,
        destination="Tokyo",
        depart=DEPART,
        return_date=None,
        travelers=1,
        currency="USD",
    )
    lisbon_jpy = await offers.flights(
        origin=None,
        destination="Lisbon",
        depart=DEPART,
        return_date=None,
        travelers=1,
        currency="JPY",
    )
    assert [o.amount for o in lisbon] != [o.amount for o in tokyo]
    assert lisbon_jpy[0].amount > lisbon[0].amount * 100
    assert lisbon[0].title.startswith("Your city to Lisbon")


async def test_hotels_have_three_tiers_scaled_to_budget() -> None:
    offers = await SampleOffers().hotels(
        destination="Pokhara",
        check_in=date(2027, 3, 10),
        check_out=date(2027, 3, 13),
        travelers=3,
        nightly_budget=Decimal("100"),
        currency="USD",
    )
    assert [o.details["tier"] for o in offers] == ["budget", "comfort", "premium"]
    nightly = [Decimal(o.details["nightly_rate"]) for o in offers]
    assert nightly == sorted(nightly)
    assert Decimal(50) <= nightly[0] <= Decimal(70)
    assert Decimal(120) <= nightly[2] <= Decimal(145)
    for offer, rate in zip(offers, nightly, strict=True):
        assert offer.details["nights"] == 3
        assert offer.details["rooms"] == 2
        assert offer.amount == (rate * 3 * 2).quantize(Decimal("0.01"))
        assert offer.provider == "Sample Stays"
        assert offer.is_sample
        assert offer.title.startswith("Pokhara ")


async def _paris_night() -> list[TravelOffer]:
    return await SampleOffers().hotels(
        destination="Paris",
        check_in=date(2027, 5, 1),
        check_out=date(2027, 5, 2),
        travelers=1,
        nightly_budget=None,
        currency="GBP",
    )


async def test_hotels_without_budget_are_stable() -> None:
    first = await _paris_night()
    assert first == await _paris_night()
    assert all(o.amount > 0 and o.currency == "GBP" for o in first)
