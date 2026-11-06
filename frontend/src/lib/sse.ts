import { type EventSourceMessage, fetchEventSource } from "@microsoft/fetch-event-source"
import { useCallback, useEffect, useRef, useState } from "react"
import { ApiError, toApiError } from "./errors"

export type AgentEventKind = "started" | "progress" | "result" | "token" | "error" | "done"

/** Mirrors backend `app/agents/events.py`. */
export interface AgentEvent {
  agent: string
  kind: AgentEventKind
  message: string
  data: Record<string, unknown> | null
}

const KINDS = new Set<AgentEventKind>(["started", "progress", "result", "token", "error", "done"])

export function parseAgentEvent(
  message: Pick<EventSourceMessage, "data" | "event">,
): AgentEvent | null {
  if (!message.data) return null
  let payload: unknown
  try {
    payload = JSON.parse(message.data)
  } catch {
    return null
  }
  if (typeof payload !== "object" || payload === null) return null
  const raw = payload as Record<string, unknown>
  const kind = (typeof raw.kind === "string" ? raw.kind : message.event) as AgentEventKind
  if (!KINDS.has(kind)) return null
  return {
    agent: typeof raw.agent === "string" ? raw.agent : "travya",
    kind,
    message: typeof raw.message === "string" ? raw.message : "",
    data:
      typeof raw.data === "object" && raw.data !== null && !Array.isArray(raw.data)
        ? (raw.data as Record<string, unknown>)
        : null,
  }
}

export interface StreamOptions {
  body: unknown
  signal: AbortSignal
  fetch: typeof fetch
  onEvent: (event: AgentEvent) => void
  /** Called once the API accepted the request and the event stream is open. */
  onOpen?: () => void
}

/**
 * POSTs and reads a server-sent event stream. Never retries: both streaming endpoints start
 * paid agent runs. HTTP errors before the stream opens reject with an ApiError; an abort resolves.
 */
export async function streamEvents(url: string, options: StreamOptions): Promise<void> {
  const { body, signal, onEvent, onOpen } = options
  try {
    await openStream(url, body, signal, options.fetch, onEvent, onOpen)
  } catch (error) {
    if (signal.aborted) return
    throw error instanceof ApiError ? error : toApiError(error, null)
  }
}

function openStream(
  url: string,
  body: unknown,
  signal: AbortSignal,
  fetchImpl: typeof fetch,
  onEvent: (event: AgentEvent) => void,
  onOpen?: () => void,
): Promise<void> {
  return fetchEventSource(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify(body),
    signal,
    fetch: fetchImpl,
    openWhenHidden: true,
    async onopen(response) {
      const type = response.headers.get("content-type") ?? ""
      if (response.ok && type.includes("text/event-stream")) {
        onOpen?.()
        return
      }
      let payload: unknown = null
      try {
        payload = await response.json()
      } catch {
        payload = null
      }
      throw toApiError(payload, response)
    },
    onmessage(message) {
      const event = parseAgentEvent(message)
      if (event) onEvent(event)
    },
    onerror(error: unknown) {
      throw error
    },
  })
}

export type StreamStatus = "idle" | "streaming" | "done" | "error" | "aborted"

/** One stream at a time per component; a new start or unmount aborts the previous one. */
export function useEventStream(fetchImpl: typeof fetch) {
  const [status, setStatus] = useState<StreamStatus>("idle")
  const [error, setError] = useState<ApiError | null>(null)
  const controller = useRef<AbortController | null>(null)

  useEffect(() => () => controller.current?.abort(), [])

  const start = useCallback(
    async (
      url: string,
      body: unknown,
      onEvent: (event: AgentEvent) => void,
      onOpen?: () => void,
    ) => {
      controller.current?.abort()
      const current = new AbortController()
      controller.current = current
      setStatus("streaming")
      setError(null)
      try {
        await streamEvents(url, {
          body,
          signal: current.signal,
          fetch: fetchImpl,
          onEvent,
          onOpen,
        })
        const outcome: StreamStatus = current.signal.aborted ? "aborted" : "done"
        if (controller.current === current) setStatus(outcome)
        return outcome
      } catch (caught) {
        const apiError = caught instanceof ApiError ? caught : toApiError(caught, null)
        if (controller.current === current) {
          setError(apiError)
          setStatus("error")
        }
        return apiError
      }
    },
    [fetchImpl],
  )

  const abort = useCallback(() => controller.current?.abort(), [])

  return { status, error, start, abort }
}
