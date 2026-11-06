import { describe, expect, it } from "vitest"
import type { AgentEvent } from "@/lib/sse"
import { describeProgress, initialTimeline, reduceTimeline, type TimelineState } from "./timeline"

const ev = (
  agent: string,
  kind: AgentEvent["kind"],
  message = "",
  data: AgentEvent["data"] = null,
): AgentEvent => ({
  agent,
  kind,
  message,
  data,
})

function run(events: Array<[number, AgentEvent]>): TimelineState {
  return events.reduce((state, [at, event]) => reduceTimeline(state, event, at), initialTimeline())
}

describe("reduceTimeline", () => {
  it("runs the four scouts in parallel and times each lane", () => {
    const state = run([
      [0, ev("travya", "started", "Planning your trip to Lisbon")],
      [10, ev("weather_scout", "started")],
      [11, ev("places_scout", "started")],
      [12, ev("guide_scout", "started")],
      [13, ev("offers_scout", "started")],
      [
        900,
        ev("places_scout", "progress", "Found 2 places", {
          places: [
            { name: "Belém Tower", category: "attraction", lat: 38.69, lon: -9.21 },
            { name: "Broken", lat: "x", lon: 1 },
          ],
        }),
      ],
    ])
    expect(state.status).toBe("running")
    const running = ["weather_scout", "guide_scout", "offers_scout"] as const
    for (const id of running) expect(state.steps[id].status).toBe("running")
    expect(state.steps.places_scout).toMatchObject({
      status: "done",
      startedAt: 11,
      finishedAt: 900,
    })
    expect(state.places).toEqual([
      { name: "Belém Tower", category: "attraction", lat: 38.69, lon: -9.21 },
    ])
  })

  it("closes silent scouts when the planner starts and keeps weather previews", () => {
    const state = run([
      [0, ev("travya", "started")],
      [1, ev("weather_scout", "started")],
      [2, ev("guide_scout", "started")],
      [
        300,
        ev("weather_scout", "progress", "Sunny", {
          weather: [
            { day: "2026-12-01", summary: "Sunny", temp_min_c: 9, temp_max_c: 17, weather_code: 0 },
          ],
        }),
      ],
      [400, ev("planner", "started")],
    ])
    expect(state.steps.guide_scout).toMatchObject({ status: "done", finishedAt: 400 })
    expect(state.steps.planner.status).toBe("running")
    expect(state.weather[0]).toMatchObject({ day: "2026-12-01", temp_max_c: 17 })
  })

  it("lists critic issues and strikes them through once the reviser runs", () => {
    const issues = ["Day 2 is too packed", "Lunch missing on day 3"]
    const afterCritic = run([
      [0, ev("travya", "started")],
      [1, ev("planner", "started")],
      [2, ev("planner", "result", "Drafted 3 days with 9 activities.")],
      [3, ev("critic", "started")],
      [4, ev("critic", "result", "Found 2 thing(s) to improve.", { issues })],
      [5, ev("quality_gate", "started")],
      [6, ev("quality_gate", "progress", "Sending 2 issue(s) back to the planner.")],
    ])
    expect(afterCritic.issues).toEqual(issues.map((text) => ({ text, round: 1, resolved: false })))
    expect(afterCritic.steps.quality_gate.message).toBe("Sending 2 issue(s) back to the planner.")

    const revised = [
      [7, ev("reviser", "started")],
      [8, ev("reviser", "result", "Revised 3 days with 9 activities.")],
      [9, ev("critic", "result", "Looks good.", { issues: [] })],
    ] as Array<[number, AgentEvent]>
    const state = revised.reduce((acc, [at, event]) => reduceTimeline(acc, event, at), afterCritic)
    expect(state.issues.every((issue) => issue.resolved)).toBe(true)
    expect(state.steps.critic.runs).toBe(2)
    expect(state.steps.reviser.status).toBe("done")
  })

  it("finishes with the trip id, or stops on an error", () => {
    const done = run([
      [0, ev("travya", "started")],
      [1, ev("planner", "started")],
      [50, ev("travya", "done", "Your 3-day itinerary is ready.", { trip_id: "t-1" })],
    ])
    expect(done).toMatchObject({
      status: "done",
      tripId: "t-1",
      headline: "Your 3-day itinerary is ready.",
      finishedAt: 50,
    })
    expect(done.steps.planner.status).toBe("done")

    const failed = run([
      [0, ev("travya", "started")],
      [9, ev("travya", "error", "Planning failed because an AI or data service is unavailable.")],
    ])
    expect(failed).toMatchObject({
      status: "error",
      error: "Planning failed because an AI or data service is unavailable.",
    })
  })

  it("ignores unknown agents and token events", () => {
    const start = run([[0, ev("travya", "started")]])
    expect(reduceTimeline(start, ev("mystery", "progress", "?"), 1)).toBe(start)
    expect(reduceTimeline(start, ev("planner", "token", "x"), 1)).toBe(start)
  })
})

describe("the map step", () => {
  const approved = (): Array<[number, AgentEvent]> => [
    [0, ev("travya", "started")],
    [1, ev("planner", "started")],
    [2, ev("planner", "result", "Drafted 3 days with 9 activities.")],
    [3, ev("critic", "started")],
    [4, ev("critic", "result", "Looks good.", { issues: [] })],
    [5, ev("quality_gate", "started")],
    [6, ev("quality_gate", "progress", "Plan approved.")],
  ]

  it("shows the geocoding tail as a running step instead of a silent timer", () => {
    const state = run([
      ...approved(),
      [7, ev("finalize", "started", "finalize started")],
      [7, ev("finalize", "progress", "Itinerary finalised.")],
    ])
    expect(state.status).toBe("running")
    expect(state.steps.finalize).toMatchObject({
      status: "running",
      message: "Placing stops on the map",
      startedAt: 7,
    })
    expect(state.steps.quality_gate.status).toBe("done")
    expect(describeProgress(state)).toBe("Placing stops on the map.")
  })

  it("takes the server's own progress message and finishes on done", () => {
    const state = run([
      ...approved(),
      [7, ev("travya", "progress", "Placing 14 stops on the map")],
      [9, ev("travya", "done", "Your 3-day itinerary is ready.", { trip_id: "t" })],
    ])
    expect(state.steps.finalize).toMatchObject({
      status: "done",
      message: "Placing 14 stops on the map",
      startedAt: 7,
      finishedAt: 9,
    })
  })
})

describe("describeProgress", () => {
  it("says what just happened, in order", () => {
    const steps: Array<[number, AgentEvent, string]> = [
      [0, ev("travya", "started", "Planning your trip to Lisbon"), "The agents are researching"],
      [1, ev("weather_scout", "started"), "The agents are researching"],
      [2, ev("places_scout", "started"), "The agents are researching"],
      [3, ev("weather_scout", "progress", "Mild."), "1 of 4 research scouts done."],
      [4, ev("places_scout", "progress", "Found 9 places."), "2 of 4 research scouts done."],
      [5, ev("planner", "started"), "The planner is drafting your days."],
      [6, ev("planner", "result", "Drafted 3 days with 9 activities."), "Drafted 3 days"],
      [7, ev("critic", "started"), "The critic is reviewing the draft."],
      [
        8,
        ev("critic", "result", "Found 2 thing(s) to improve.", { issues: ["a", "b"] }),
        "The critic found 2 issues.",
      ],
      [9, ev("reviser", "started"), "The reviser is fixing the critic's issues."],
      [9.5, ev("reviser", "result", "Revised 3 days with 9 activities."), "Revised 3 days"],
      [10, ev("critic", "result", "Looks good.", { issues: [] }), "The critic approved the plan."],
      [
        11,
        ev("travya", "done", "Your 3-day itinerary is ready."),
        "Your 3-day itinerary is ready.",
      ],
    ]
    let state = initialTimeline()
    for (const [at, event, expected] of steps) {
      state = reduceTimeline(state, event, at)
      expect(describeProgress(state)).toContain(expected)
    }
    const failed = reduceTimeline(state, ev("travya", "error", "Gemini is overloaded."), 12)
    expect(describeProgress(failed)).toBe("Planning stopped. Gemini is overloaded.")
  })
})
