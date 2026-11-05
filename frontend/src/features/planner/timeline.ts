import type { AgentEvent } from "@/lib/sse"

/**
 * Folds the planning SSE stream (backend `PlanningService._translate`) into what the timeline shows:
 * four scout lanes that run in parallel, then planner → critic → quality gate → reviser rounds.
 */

export const SCOUTS = ["weather_scout", "places_scout", "guide_scout", "offers_scout"] as const
export type ScoutId = (typeof SCOUTS)[number]

export const STAGES = ["planner", "critic", "quality_gate", "reviser"] as const
export type StageId = (typeof STAGES)[number]

export const AGENT_LABELS: Record<ScoutId | StageId, string> = {
  weather_scout: "Weather",
  places_scout: "Places",
  guide_scout: "Guide",
  offers_scout: "Booking",
  planner: "Planner",
  critic: "Critic",
  quality_gate: "Quality gate",
  reviser: "Reviser",
}

export type StepStatus = "pending" | "running" | "done" | "error"

export interface Step {
  status: StepStatus
  message: string
  startedAt: number | null
  finishedAt: number | null
  /** How many results this agent produced (critic and reviser can run twice). */
  runs: number
}

export interface Issue {
  text: string
  round: number
  resolved: boolean
}

export interface PreviewPlace {
  name: string
  category: string | null
  lat: number
  lon: number
}

export interface PreviewWeather {
  day: string
  summary: string
  temp_min_c: number | null
  temp_max_c: number | null
  weather_code: number | null
}

export interface TimelineState {
  status: "idle" | "running" | "done" | "error"
  startedAt: number | null
  finishedAt: number | null
  steps: Record<ScoutId | StageId, Step>
  issues: Issue[]
  places: PreviewPlace[]
  weather: PreviewWeather[]
  sources: string[]
  offers: number | null
  headline: string
  error: string | null
  tripId: string | null
}

const idleStep = (): Step => ({
  status: "pending",
  message: "",
  startedAt: null,
  finishedAt: null,
  runs: 0,
})

export function initialTimeline(): TimelineState {
  const steps = Object.fromEntries([...SCOUTS, ...STAGES].map((id) => [id, idleStep()])) as Record<
    ScoutId | StageId,
    Step
  >
  return {
    status: "idle",
    startedAt: null,
    finishedAt: null,
    steps,
    issues: [],
    places: [],
    weather: [],
    sources: [],
    offers: null,
    headline: "",
    error: null,
    tripId: null,
  }
}

const isKnown = (agent: string): agent is ScoutId | StageId => agent in AGENT_LABELS
const isScout = (agent: string): agent is ScoutId => (SCOUTS as readonly string[]).includes(agent)

function num(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null
}

function str(value: unknown): string | null {
  return typeof value === "string" ? value : null
}

function readPlaces(value: unknown): PreviewPlace[] {
  if (!Array.isArray(value)) return []
  return value.flatMap((raw) => {
    const place = raw as Record<string, unknown>
    const lat = num(place.lat)
    const lon = num(place.lon)
    const name = str(place.name)
    return lat === null || lon === null || !name
      ? []
      : [{ name, category: str(place.category), lat, lon }]
  })
}

function readWeather(value: unknown): PreviewWeather[] {
  if (!Array.isArray(value)) return []
  return value.flatMap((raw) => {
    const day = raw as Record<string, unknown>
    const date = str(day.day)
    return date
      ? [
          {
            day: date,
            summary: str(day.summary) ?? "",
            temp_min_c: num(day.temp_min_c),
            temp_max_c: num(day.temp_max_c),
            weather_code: num(day.weather_code),
          },
        ]
      : []
  })
}

function finishRunning(steps: TimelineState["steps"], at: number, only?: readonly string[]) {
  const next = { ...steps }
  for (const id of Object.keys(next) as (ScoutId | StageId)[]) {
    if (only && !only.includes(id)) continue
    const step = next[id]
    if (step.status === "running") next[id] = { ...step, status: "done", finishedAt: at }
  }
  return next
}

export function reduceTimeline(state: TimelineState, event: AgentEvent, at: number): TimelineState {
  const { agent, kind } = event

  if (agent === "travya") {
    if (kind === "started") {
      return { ...initialTimeline(), status: "running", startedAt: at, headline: event.message }
    }
    if (kind === "done") {
      return {
        ...state,
        status: "done",
        finishedAt: at,
        steps: finishRunning(state.steps, at),
        issues: state.issues,
        headline: event.message,
        tripId: str(event.data?.trip_id),
      }
    }
    if (kind === "error") {
      return {
        ...state,
        status: "error",
        finishedAt: at,
        error: event.message || "Planning failed.",
      }
    }
    return state
  }

  if (!isKnown(agent)) return state
  let steps = { ...state.steps }
  const step = steps[agent]

  // The research stage is over once any later agent starts; close lanes that never reported.
  if (!isScout(agent) && kind === "started") steps = finishRunning(steps, at, SCOUTS)

  if (kind === "started") {
    steps[agent] = { ...step, status: "running", startedAt: step.startedAt ?? at, finishedAt: null }
    return { ...state, status: "running", startedAt: state.startedAt ?? at, steps }
  }

  if (kind === "error") {
    steps[agent] = { ...step, status: "error", message: event.message, finishedAt: at }
    return { ...state, steps }
  }

  if (kind !== "progress" && kind !== "result") return state

  steps[agent] = {
    ...step,
    status: "done",
    message: event.message,
    startedAt: step.startedAt ?? at,
    finishedAt: at,
    runs: step.runs + 1,
  }
  const next: TimelineState = { ...state, steps, headline: event.message }
  const data = event.data ?? {}

  if (agent === "places_scout" && "places" in data) next.places = readPlaces(data.places)
  if (agent === "weather_scout" && "weather" in data) next.weather = readWeather(data.weather)
  if (agent === "guide_scout" && Array.isArray(data.sources)) {
    next.sources = data.sources.filter((url): url is string => typeof url === "string")
  }
  if (agent === "offers_scout") next.offers = num(data.offers)

  if (agent === "critic") {
    const round = step.runs + 1
    const found = Array.isArray(data.issues)
      ? data.issues.filter((text): text is string => typeof text === "string")
      : []
    next.issues = [...state.issues, ...found.map((text) => ({ text, round, resolved: false }))]
  }
  if (agent === "reviser") {
    next.issues = state.issues.map((issue) => ({ ...issue, resolved: true }))
  }
  return next
}

/** Replays a list of `[offsetMs, event]` pairs, e.g. for the landing page demo. */
export function replay(events: Array<[number, AgentEvent]>, upTo: number): TimelineState {
  return events
    .filter(([offset]) => offset <= upTo)
    .reduce((state, [offset, event]) => reduceTimeline(state, event, offset), initialTimeline())
}
