import { useSyncExternalStore } from "react"
import { ApiError } from "./errors"

/**
 * The API runs on a free Hugging Face Space that sleeps when idle; the first requests after a
 * quiet spell fail (the Space's own 503 page carries no CORS headers, so the browser reports a
 * network error) for the minute or two it takes to wake. Instead of "You're offline", poll the
 * health endpoint with back-off, show "Waking up the free server…" and retry reads once it is up.
 */

export type WakeStatus = "idle" | "waking" | "awake" | "failed"

export interface WakeOptions {
  /** `/api/v1/health/live` on the API. */
  healthUrl: string
  fetch?: typeof fetch
  /** Delays between polls; the last one repeats until `timeoutMs`. */
  delaysMs?: number[]
  timeoutMs?: number
  sleep?: (ms: number) => Promise<void>
  now?: () => number
}

const DEFAULT_DELAYS = [1000, 2000, 3000, 5000, 8000]
const DEFAULT_TIMEOUT = 180_000

let status: WakeStatus = "idle"
let since: number | null = null
let inFlight: Promise<boolean> | null = null
const listeners = new Set<() => void>()

function setStatus(next: WakeStatus) {
  status = next
  since = next === "waking" ? Date.now() : since
  for (const listener of listeners) listener()
}

const wait = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms))

async function isLive(url: string, fetchImpl: typeof fetch): Promise<boolean> {
  try {
    const response = await fetchImpl(url, {
      cache: "no-store",
      signal: AbortSignal.timeout(15_000),
    })
    return response.ok
  } catch {
    return false
  }
}

/** Polls until the API answers; one poll loop at a time however many requests failed. */
export function wakeServer(options: WakeOptions): Promise<boolean> {
  if (inFlight) return inFlight
  const fetchImpl = options.fetch ?? ((input, init) => globalThis.fetch(input, init))
  const delays = options.delaysMs ?? DEFAULT_DELAYS
  const timeout = options.timeoutMs ?? DEFAULT_TIMEOUT
  const sleep = options.sleep ?? wait
  const now = options.now ?? Date.now
  setStatus("waking")
  inFlight = (async () => {
    const started = now()
    for (let attempt = 0; ; attempt += 1) {
      if (await isLive(options.healthUrl, fetchImpl)) {
        setStatus("awake")
        return true
      }
      if (now() - started >= timeout) {
        setStatus("failed")
        return false
      }
      await sleep(delays[Math.min(attempt, delays.length - 1)] ?? 5000)
    }
  })().finally(() => {
    inFlight = null
  })
  return inFlight
}

/** Fire-and-forget request that starts waking the Space early (e.g. from the landing page). */
export function warmServer(healthUrl: string, fetchImpl: typeof fetch = globalThis.fetch) {
  if (status !== "idle") return
  try {
    void fetchImpl(healthUrl, { cache: "no-store", keepalive: true }).catch(() => undefined)
  } catch {
    // Older browsers without keepalive: nothing to do.
  }
}

/** The Space's own placeholder while asleep or restarting (not a JSON answer from the API). */
function looksAsleep(response: Response): boolean {
  if (![502, 503, 504].includes(response.status)) return false
  return !(response.headers.get("content-type") ?? "").includes("json")
}

function isAbort(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError"
}

export const WOKE_TITLE = "The server was asleep"
export const WOKE_DETAIL = "The free server was asleep and is awake now. Please try again."

/**
 * Wraps fetch: when the API looks asleep, wait for it to wake. Reads are then retried once; writes
 * (which may start paid agent runs) are not, and fail with a "try again" error instead.
 */
export function withWakeUp(baseFetch: typeof fetch, wake: () => Promise<boolean>): typeof fetch {
  return async (input, init) => {
    const request = new Request(input, init)
    const safe = request.method === "GET" || request.method === "HEAD"
    const spare = safe ? request.clone() : null
    let response: Response
    try {
      response = await baseFetch(request)
    } catch (error) {
      if (isAbort(error) || request.signal.aborted) throw error
      if (!(await wake())) throw error
      if (spare) return baseFetch(spare)
      throw new ApiError({ status: 0, title: WOKE_TITLE, detail: WOKE_DETAIL })
    }
    if (!looksAsleep(response)) return response
    if (!(await wake())) return response
    if (spare) return baseFetch(spare)
    throw new ApiError({ status: 0, title: WOKE_TITLE, detail: WOKE_DETAIL })
  }
}

export function useWakeStatus(): { status: WakeStatus; since: number | null } {
  const current = useSyncExternalStore(
    (listener) => {
      listeners.add(listener)
      return () => listeners.delete(listener)
    },
    () => status,
    () => "idle" as WakeStatus,
  )
  return { status: current, since }
}

export function wakeStatus(): WakeStatus {
  return status
}

/** Tests only. */
export function resetWake() {
  status = "idle"
  since = null
  inFlight = null
  for (const listener of listeners) listener()
}
