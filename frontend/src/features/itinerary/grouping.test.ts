import { describe, expect, it } from "vitest"
import type { ItineraryItemRead } from "@/client/types.gen"
import { groupByDay, totalEstimatedCost } from "./grouping"

let next = 0
const item = (
  day: string,
  position: number,
  start_time: string | null = null,
  title = `Item ${next}`,
): ItineraryItemRead => ({
  id: `id-${next++}`,
  trip_id: "t",
  day,
  position,
  start_time,
  end_time: null,
  title,
  description: null,
  category: "sight",
  place_name: null,
  latitude: null,
  longitude: null,
  estimated_cost: null,
  source: "agent",
})

describe("groupByDay", () => {
  it("returns every trip day in order, including empty ones", () => {
    const groups = groupByDay([item("2026-12-03", 0)], "2026-12-01", "2026-12-03")
    expect(groups.map((group) => [group.day, group.dayIndex, group.items.length])).toEqual([
      ["2026-12-01", 1, 0],
      ["2026-12-02", 2, 0],
      ["2026-12-03", 3, 1],
    ])
  })

  it("sorts by position, then start time, and drops items outside the trip", () => {
    const groups = groupByDay(
      [
        item("2026-12-01", 1, "09:00:00", "Second"),
        item("2026-12-01", 0, "18:00:00", "First"),
        item("2026-12-01", 1, "08:00:00", "Also second, earlier"),
        item("2026-11-30", 0, null, "Before the trip"),
      ],
      "2026-12-01",
      "2026-12-01",
    )
    expect(groups).toHaveLength(1)
    expect(groups[0]?.items.map((entry) => entry.title)).toEqual([
      "First",
      "Also second, earlier",
      "Second",
    ])
  })

  it("crosses month boundaries without time zone drift", () => {
    const groups = groupByDay([], "2026-12-30", "2027-01-02")
    expect(groups.map((group) => group.day)).toEqual([
      "2026-12-30",
      "2026-12-31",
      "2027-01-01",
      "2027-01-02",
    ])
  })
})

describe("totalEstimatedCost", () => {
  it("adds decimal strings and skips missing values", () => {
    const items = [item("2026-12-01", 0), item("2026-12-01", 1), item("2026-12-01", 2)]
    items[0] = { ...items[0], estimated_cost: "12.50" } as ItineraryItemRead
    items[1] = { ...items[1], estimated_cost: "7.25" } as ItineraryItemRead
    expect(totalEstimatedCost(items)).toBeCloseTo(19.75)
  })
})
