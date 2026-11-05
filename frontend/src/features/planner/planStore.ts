import type { QueryClient } from "@tanstack/react-query"
import { useSyncExternalStore } from "react"
import { apiFetch, apiUrl } from "@/lib/api"
import { ApiError, toApiError } from "@/lib/errors"
import { notifyError, notifySuccess } from "@/lib/notify"
import { invalidateTrip } from "@/lib/queryKeys"
import { streamEvents } from "@/lib/sse"
import { initialTimeline, reduceTimeline, type TimelineState } from "./timeline"

/**
 * Planning runs live outside React so they survive navigation (new-trip form → trip page) and
 * StrictMode double effects: one POST per run, ever.
 */
export interface PlanRun {
  state: TimelineState
  error: ApiError | null
  active: boolean
  /** Re-plan instructions of this run, reused by "Try again". */
  instructions: string | null
}

export const STOPPED_MESSAGE = "You stopped planning. The trip keeps its previous plan."

const runs = new Map<string, PlanRun>()
const controllers = new Map<string, AbortController>()
const listeners = new Set<() => void>()

function set(tripId: string, update: (run: PlanRun) => PlanRun) {
  const current = runs.get(tripId)
  if (!current) return
  runs.set(tripId, update(current))
  for (const listener of listeners) listener()
}

export function startPlan(queryClient: QueryClient, tripId: string, instructions?: string | null) {
  if (runs.get(tripId)?.active) return
  const kept = instructions?.trim() || null
  const state = { ...initialTimeline(), status: "running" as const, startedAt: Date.now() }
  runs.set(tripId, { state, error: null, active: true, instructions: kept })
  for (const listener of listeners) listener()

  const controller = new AbortController()
  controllers.set(tripId, controller)
  let refreshed = false
  streamEvents(apiUrl(`/api/v1/trips/${tripId}/plan`), {
    body: { instructions: kept },
    signal: controller.signal,
    fetch: apiFetch,
    onEvent: (event) => {
      // The trip flips to "planning" as soon as the stream opens.
      if (!refreshed) {
        refreshed = true
        void invalidateTrip(queryClient, tripId)
      }
      set(tripId, (run) => ({ ...run, state: reduceTimeline(run.state, event, Date.now()) }))
      if (event.agent === "travya" && event.kind === "done") {
        notifySuccess("Itinerary ready", event.message)
      }
    },
  })
    .then(() => {
      const stopped = controller.signal.aborted
      set(tripId, (run) =>
        run.state.status === "running"
          ? {
              ...run,
              active: false,
              state: {
                ...run.state,
                status: "error",
                finishedAt: Date.now(),
                error: stopped
                  ? STOPPED_MESSAGE
                  : "The planning stream ended early. Please re-plan.",
              },
            }
          : { ...run, active: false },
      )
    })
    .catch((caught: unknown) => {
      const error = caught instanceof ApiError ? caught : toApiError(caught, null)
      set(tripId, (run) => ({
        ...run,
        active: false,
        error,
        state: { ...run.state, status: "error", error: error.detail },
      }))
      notifyError(error, "Couldn't start planning")
    })
    .finally(() => {
      if (controllers.get(tripId) === controller) controllers.delete(tripId)
      void invalidateTrip(queryClient, tripId)
    })
}

/** Aborts this tab's run; the API puts the trip back to its previous status. */
export function stopPlan(tripId: string) {
  controllers.get(tripId)?.abort()
}

/** Starts the same run again, with the instructions it had. */
export function retryPlan(queryClient: QueryClient, tripId: string) {
  startPlan(queryClient, tripId, runs.get(tripId)?.instructions ?? null)
}

export function dismissPlan(tripId: string) {
  if (runs.get(tripId)?.active) return
  runs.delete(tripId)
  for (const listener of listeners) listener()
}

function subscribe(listener: () => void) {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export function usePlanRun(tripId: string): PlanRun | undefined {
  return useSyncExternalStore(
    subscribe,
    () => runs.get(tripId),
    () => undefined,
  )
}
