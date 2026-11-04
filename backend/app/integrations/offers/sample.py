"""Deterministic sample flights and hotels.

Travya does not sell travel: these offers are illustrative, labelled `is_sample=True` and stable for
the same destination and dates so plans and screenshots do not change between runs.
"""

import hashlib
import random
from datetime import date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal
from math import ceil

from app.integrations.ports import TravelOffer

CENT = Decimal("0.01")
SAMPLE_NOTE = "Illustrative sample fare; Travya does not sell travel."
# Rough units per US dollar, only so sample prices look plausible in common currencies.
USD_RATES: dict[str, Decimal] = {
    "USD": Decimal(1),
    "EUR": Decimal("0.92"),
    "GBP": Decimal("0.79"),
    "CHF": Decimal("0.88"),
    "CAD": Decimal("1.37"),
    "AUD": Decimal("1.52"),
    "JPY": Decimal(150),
    "CNY": Decimal("7.2"),
    "SGD": Decimal("1.34"),
    "AED": Decimal("3.67"),
    "THB": Decimal(35),
    "INR": Decimal(84),
    "NPR": Decimal(134),
}
# airline, flight-number prefix, stops, price factor
_FLIGHT_OPTIONS = (
    ("Sample Air", "SA", 0, 1.25),
    ("Sample Jet", "SJ", 1, 0.85),
    ("Sample Wings", "SW", 1, 1.0),
)
_STOPS = {0: "nonstop", 1: "1 stop"}
_HOTEL_WORDS = (
    "Courtyard",
    "Garden",
    "Heritage",
    "Riverside",
    "Old Town",
    "Skyline",
    "Lotus",
    "Central",
)
# tier, stars, kinds, share of the nightly budget, USD range without a budget
_HOTEL_TIERS = (
    ("budget", 2, ("Guesthouse", "Hostel"), Decimal("0.6"), (30, 60)),
    ("comfort", 3, ("Hotel", "Inn"), Decimal("0.9"), (85, 150)),
    ("premium", 5, ("Grand Hotel", "Suites"), Decimal("1.3"), (220, 420)),
)


def _rng(*parts: object) -> random.Random:
    seed = hashlib.blake2b("|".join(map(str, parts)).encode(), digest_size=8).digest()
    return random.Random(int.from_bytes(seed))  # noqa: S311


def _money(amount: Decimal | float) -> Decimal:
    return Decimal(str(amount)).quantize(CENT, rounding=ROUND_HALF_UP)


def _usd_rate(currency: str) -> Decimal:
    return USD_RATES.get(currency.upper(), Decimal(1))


class SampleOffers:
    async def flights(
        self,
        *,
        origin: str | None,
        destination: str,
        depart: date,
        return_date: date | None,
        travelers: int,
        currency: str,
    ) -> list[TravelOffer]:
        travelers = max(travelers, 1)
        rng = _rng(
            "flights", (origin or "").casefold(), destination.casefold(), depart, return_date
        )
        base_usd = rng.uniform(140, 780)
        base_minutes = rng.randrange(90, 13 * 60, 5)
        offers: list[TravelOffer] = []
        for airline, code, stops, price_factor in _FLIGHT_OPTIONS:
            fare_usd = base_usd * price_factor * (1.85 if return_date else 1.0)
            per_traveler = _money(Decimal(fare_usd) * _usd_rate(currency))
            minute = rng.choice((0, 15, 30, 45))
            departs = datetime.combine(depart, time(rng.randrange(5, 22), minute))
            minutes = base_minutes + stops * rng.randrange(75, 240, 5)
            arrives = departs + timedelta(minutes=minutes)
            offers.append(
                TravelOffer(
                    kind="flight",
                    title=f"{origin or 'Your city'} to {destination}, {_STOPS[stops]}",
                    provider=airline,
                    amount=_money(per_traveler * travelers),
                    currency=currency.upper(),
                    details={
                        "flight_number": f"{code} {rng.randrange(100, 999)}",
                        "origin": origin,
                        "destination": destination,
                        "departs_at": departs.isoformat(timespec="minutes"),
                        "arrives_at": arrives.isoformat(timespec="minutes"),
                        "duration_minutes": minutes,
                        "stops": stops,
                        "cabin": "economy",
                        "return_date": return_date.isoformat() if return_date else None,
                        "travelers": travelers,
                        "price_per_traveler": str(per_traveler),
                        "note": SAMPLE_NOTE,
                    },
                    is_sample=True,
                )
            )
        return sorted(offers, key=lambda offer: offer.amount)

    async def hotels(
        self,
        *,
        destination: str,
        check_in: date,
        check_out: date,
        travelers: int,
        nightly_budget: Decimal | None,
        currency: str,
    ) -> list[TravelOffer]:
        nights = max((check_out - check_in).days, 1)
        rooms = ceil(max(travelers, 1) / 2)
        rng = _rng("hotels", destination.casefold(), check_in, check_out)
        offers: list[TravelOffer] = []
        for tier, stars, kinds, budget_share, usd_range in _HOTEL_TIERS:
            jitter = Decimal(str(round(rng.uniform(0.92, 1.08), 3)))
            if nightly_budget is not None:
                nightly = _money(nightly_budget * budget_share * jitter)
            else:
                nightly = _money(Decimal(rng.uniform(*usd_range)) * _usd_rate(currency))
            name = f"{destination} {rng.choice(_HOTEL_WORDS)} {rng.choice(kinds)}"
            offers.append(
                TravelOffer(
                    kind="hotel",
                    title=name,
                    provider="Sample Stays",
                    amount=_money(nightly * nights * rooms),
                    currency=currency.upper(),
                    details={
                        "tier": tier,
                        "stars": stars,
                        "nightly_rate": str(nightly),
                        "nights": nights,
                        "rooms": rooms,
                        "check_in": check_in.isoformat(),
                        "check_out": check_out.isoformat(),
                        "guest_rating": round(rng.uniform(7.4, 9.6), 1),
                        "free_cancellation": rng.random() < 0.6,
                        "breakfast_included": tier != "budget" and rng.random() < 0.7,
                        "note": SAMPLE_NOTE,
                    },
                    is_sample=True,
                )
            )
        return offers
