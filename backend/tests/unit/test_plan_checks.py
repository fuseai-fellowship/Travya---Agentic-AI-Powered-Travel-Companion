from app.agents.planning.checks import check_plan
from app.agents.planning.offline import scripted_plan

TRIP = {
    "destination": "Lisbon",
    "start_date": "2027-05-01",
    "end_date": "2027-05-03",
    "pace": "balanced",
    "budget": "900",
    "currency": "EUR",
    "travelers": 2,
}
PLACES = [
    {"name": "Belém Tower", "category": "attraction", "lat": 38.69, "lon": -9.21},
    {"name": "Jerónimos Monastery", "category": "religious", "lat": 38.69, "lon": -9.20},
    {"name": "Time Out Market", "category": "restaurant", "lat": 38.70, "lon": -9.14},
]


def test_scripted_plan_passes_hard_checks() -> None:
    plan = scripted_plan(TRIP, PLACES)
    assert [d.date for d in plan.days] == ["2027-05-01", "2027-05-02", "2027-05-03"]
    assert check_plan(plan.model_dump(mode="json"), TRIP) == []


def test_missing_and_extra_days_are_reported() -> None:
    plan = scripted_plan(TRIP, PLACES).model_dump(mode="json")
    plan["days"][1]["date"] = "2027-06-01"
    issues = check_plan(plan, TRIP)
    assert any("Missing days: 2027-05-02" in i for i in issues)
    assert any("outside the trip dates: 2027-06-01" in i for i in issues)


def test_pace_and_budget_are_enforced() -> None:
    plan = scripted_plan(TRIP, PLACES).model_dump(mode="json")
    plan["days"][0]["activities"] = plan["days"][0]["activities"][:1]
    plan["estimated_total"] = 5000
    issues = check_plan(plan, TRIP)
    assert any("non-meal activities" in i for i in issues)
    assert any("exceeds the budget" in i for i in issues)


def test_empty_or_malformed_plan() -> None:
    assert check_plan(None, TRIP) == ["The planner produced no plan."]
    assert "does not match the schema" in check_plan({"summary": "x"}, TRIP)[0]


def test_every_interest_the_web_app_offers_maps_to_places() -> None:
    from app.agents.planning.scouts import INTEREST_CATEGORIES

    offered = [
        "culture", "food", "nature", "history", "art", "architecture",
        "viewpoints", "nightlife", "shopping", "adventure", "relaxation", "family",
    ]  # fmt: skip
    assert [i for i in offered if not INTEREST_CATEGORIES.get(i)] == []
