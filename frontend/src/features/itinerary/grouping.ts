import type { ItineraryItemRead } from "@/client/types.gen"
import { addDays, daysBetween } from "@/lib/format"

export interface DayGroup {
  day: string
  /** 1-based day of the trip, matching the map's `day_index`. */
  dayIndex: number
  items: ItineraryItemRead[]
}

/** By start time (untimed items last), then by the planner's order, then by title. */
export function compareItems(a: ItineraryItemRead, b: ItineraryItemRead): number {
  const at = a.start_time ?? "99"
  const bt = b.start_time ?? "99"
  if (at !== bt) return at < bt ? -1 : 1
  if (a.position !== b.position) return a.position - b.position
  return a.title.localeCompare(b.title)
}

/** Every day of the trip in order (empty days included), each with its items sorted. */
export function groupByDay(items: ItineraryItemRead[], start: string, end: string): DayGroup[] {
  const length = Math.max(1, daysBetween(start, end) + 1)
  const groups: DayGroup[] = Array.from({ length }, (_, index) => ({
    day: addDays(start, index),
    dayIndex: index + 1,
    items: [],
  }))
  const byDay = new Map(groups.map((group) => [group.day, group]))
  for (const item of items) {
    const group = byDay.get(item.day)
    if (group) group.items.push(item)
  }
  for (const group of groups) group.items.sort(compareItems)
  return groups
}

export function totalEstimatedCost(items: ItineraryItemRead[]): number {
  return items.reduce((sum, item) => {
    const cost =
      item.estimated_cost === null || item.estimated_cost === undefined
        ? 0
        : Number(item.estimated_cost)
    return Number.isFinite(cost) ? sum + cost : sum
  }, 0)
}
