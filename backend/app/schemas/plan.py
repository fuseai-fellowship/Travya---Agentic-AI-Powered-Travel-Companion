"""Structured output of the planning agents (Gemini `response_schema`).

Kept flat and explicit so the model fills it reliably; dates/times are ISO strings that the service
validates before persisting.
"""

from pydantic import BaseModel, Field

from app.models import ItemCategory


class PlannedActivity(BaseModel):
    start_time: str | None = Field(default=None, description="24h HH:MM")
    end_time: str | None = Field(default=None, description="24h HH:MM")
    title: str = Field(description="Short name, e.g. 'Swayambhunath Stupa at sunrise'")
    description: str = Field(
        description="One or two sentences: what to do and why it fits the traveler"
    )
    category: ItemCategory
    place_name: str | None = Field(
        default=None, description="Exact name of a place from the research context"
    )
    estimated_cost: float | None = Field(
        default=None, description="Per group, in the trip currency"
    )


class PlannedDay(BaseModel):
    date: str = Field(description="ISO date YYYY-MM-DD within the trip dates")
    theme: str = Field(description="A short theme for the day")
    activities: list[PlannedActivity]


class BudgetBreakdown(BaseModel):
    """Explicit fields: the Gemini API does not accept free-form maps in response schemas."""

    lodging: float | None = None
    food: float | None = None
    activities: float | None = None
    transport: float | None = None


class TripPlan(BaseModel):
    summary: str = Field(description="Three to four sentences describing the trip")
    days: list[PlannedDay]
    estimated_total: float | None = Field(
        default=None, description="Total estimated cost in the trip currency"
    )
    budget_breakdown: BudgetBreakdown = Field(
        default_factory=lambda: BudgetBreakdown(),
        description="Estimated cost per category in the trip currency",
    )
    packing_tips: list[str] = Field(default_factory=list, max_length=8)
    local_tips: list[str] = Field(
        default_factory=list, max_length=8, description="Customs, safety, etiquette"
    )


class Critique(BaseModel):
    approved: bool = Field(description="True when the plan needs no changes")
    issues: list[str] = Field(
        default_factory=list, description="Concrete problems to fix, empty when approved"
    )
