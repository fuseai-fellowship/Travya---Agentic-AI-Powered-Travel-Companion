import type { AgentEvent } from "@/lib/sse"
import galleryJson from "./data/gallery.json"
import replayJson from "./data/replay-kyoto.json"

/**
 * Recorded production runs (https://travya-app.pages.dev, free-tier Gemini), captured from the
 * planning SSE stream with the browser's own timestamps. Ids and user data are stripped; nothing
 * is edited or invented. Positions are pixels on the static basemap rendered for the same run.
 */

export interface MapStop {
  day: number
  title: string
  place: string | null
  x: number
  y: number
}

export interface ProjectedMap {
  width: number
  height: number
  places?: Array<[number, number]>
  stops: MapStop[]
  routes: Array<{ day: number; points: Array<[number, number]> }>
}

export interface RecordedRun {
  destination: string
  days: number
  travelers: number
  pace: string
  interests: string[]
  recordedAt: string
  durationMs: number
  events: Array<[number, AgentEvent]>
  map: ProjectedMap
}

export interface PlanItem {
  time: string | null
  title: string
  place: string | null
  placeNe?: string
  category: string
  cost: string | null
  mapped: boolean
}

export interface GalleryPlan {
  id: string
  destination: string
  destinationNe?: string
  countryCode: string
  title: string
  startDate: string
  endDate: string
  travelers: number
  budget: string | null
  currency: string
  pace: string
  interests: string[]
  recordedAt: string
  durationMs: number
  summary: string
  estimatedTotal: number | null
  critic: { rounds: number; revisions: number; issues: number }
  days: Array<{ day: number; date: string; theme: string | null; items: PlanItem[] }>
  map: ProjectedMap
}

export const HERO_RUN = replayJson as unknown as RecordedRun
export const GALLERY = galleryJson as unknown as GalleryPlan[]

/** "5 Nov 2026" in UTC, so every visitor sees the date the run was recorded on the server. */
export function recordedOn(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  })
}
