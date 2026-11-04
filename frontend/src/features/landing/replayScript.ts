import type { AgentEvent } from "@/lib/sse"

const event = (
  agent: string,
  kind: AgentEvent["kind"],
  message = "",
  data: AgentEvent["data"] = null,
): AgentEvent => ({ agent, kind, message, data })

/** Kathmandu places for the replay map (OpenStreetMap coordinates). */
export const REPLAY_PLACES = [
  { name: "Kathmandu Durbar Square", category: "attraction", lat: 27.7045, lon: 85.3077 },
  { name: "Swayambhunath", category: "religious", lat: 27.7149, lon: 85.2903 },
  { name: "Boudhanath", category: "religious", lat: 27.7215, lon: 85.362 },
  { name: "Pashupatinath", category: "religious", lat: 27.7105, lon: 85.3487 },
  { name: "Garden of Dreams", category: "park", lat: 27.7142, lon: 85.3145 },
  { name: "Asan Tole", category: "shopping", lat: 27.7077, lon: 85.3115 },
  { name: "Patan Durbar Square", category: "attraction", lat: 27.6727, lon: 85.3253 },
  { name: "Patan Museum", category: "museum", lat: 27.6731, lon: 85.3249 },
  { name: "Thamel", category: "nightlife", lat: 27.7154, lon: 85.3123 },
  { name: "Kopan Monastery", category: "religious", lat: 27.7425, lon: 85.3624 },
  { name: "Bhaktapur Durbar Square", category: "attraction", lat: 27.6722, lon: 85.428 },
  { name: "Nyatapola Temple", category: "religious", lat: 27.6716, lon: 85.4294 },
]

/** Stops per day once the plan is ready (indexes into REPLAY_PLACES). */
export const REPLAY_DAYS = [
  [0, 5, 4, 8],
  [1, 3, 2],
  [6, 7],
  [10, 11],
]

const WEATHER = [
  ["Mostly sunny", 9, 22, 1],
  ["Partly cloudy", 10, 21, 2],
  ["Afternoon showers", 11, 19, 61],
  ["Mostly sunny", 9, 22, 1],
].map(([summary, min, max, code], index) => ({
  day: `2026-03-0${index + 2}`,
  summary,
  temp_min_c: min,
  temp_max_c: max,
  weather_code: code,
}))

/** A scripted replay of a planning run's event stream (same shapes the API sends). */
export const REPLAY_SCRIPT: Array<[number, AgentEvent]> = [
  [0, event("travya", "started", "Planning your trip to Kathmandu")],
  [150, event("weather_scout", "started")],
  [200, event("places_scout", "started")],
  [250, event("guide_scout", "started")],
  [300, event("offers_scout", "started")],
  [
    1300,
    event("weather_scout", "progress", "4-day outlook: mild, showers on day 3.", {
      weather: WEATHER,
    }),
  ],
  [
    1900,
    event("places_scout", "progress", "Found 12 places on OpenStreetMap.", {
      places: REPLAY_PLACES,
    }),
  ],
  [2300, event("guide_scout", "progress", "3 Wikivoyage passages on Kathmandu.", { sources: [] })],
  [
    2700,
    event("offers_scout", "progress", "Collected 4 sample stay and flight quotes.", { offers: 4 }),
  ],
  [2900, event("planner", "started")],
  [4300, event("planner", "result", "Drafted 4 days with 11 activities.")],
  [4500, event("critic", "started")],
  [
    5500,
    event("critic", "result", "Found 2 thing(s) to improve.", {
      issues: ["Day 2 crosses the valley twice; group the stupas", "Day 3 has no lunch stop"],
    }),
  ],
  [5700, event("quality_gate", "started")],
  [5800, event("quality_gate", "progress", "Sending 2 issue(s) back to the planner.")],
  [6000, event("reviser", "started")],
  [7300, event("reviser", "result", "Revised 4 days with 11 activities.")],
  [8100, event("critic", "result", "Looks good.", { issues: [] })],
  [8300, event("quality_gate", "progress", "Plan approved.")],
  [8600, event("travya", "done", "Your 4-day itinerary is ready.", { trip_id: "replay" })],
]

export const REPLAY_LENGTH = 8600
