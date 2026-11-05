"""Agent activity events streamed to the browser over SSE."""

from typing import Any, Literal

from pydantic import BaseModel

EventKind = Literal["started", "progress", "result", "token", "error", "done"]


class AgentEvent(BaseModel):
    agent: str
    kind: EventKind
    message: str = ""
    data: dict[str, Any] | None = None

    def sse(self) -> dict[str, str]:
        return {"event": self.kind, "data": self.model_dump_json()}


AGENT_LABELS = {
    "weather_scout": "Weather scout",
    "places_scout": "Places scout",
    "guide_scout": "Guide researcher",
    "offers_scout": "Booking scout",
    "planner": "Itinerary planner",
    "critic": "Critic",
    "quality_gate": "Quality gate",
    "reviser": "Reviser",
    "assistant": "Travel assistant",
    "travya": "Travya",
}
