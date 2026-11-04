import { describe, expect, it } from "vitest"
import type { AgentEvent } from "@/lib/sse"
import { initialTimeline, reduceTimeline, type TimelineState } from "./timeline"

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
