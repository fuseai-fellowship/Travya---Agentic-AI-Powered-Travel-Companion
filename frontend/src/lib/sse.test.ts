import { act, renderHook, waitFor } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"
import { ApiError } from "./errors"
import { type AgentEvent, parseAgentEvent, streamEvents, useEventStream } from "./sse"

const encoder = new TextEncoder()

/** A fetch whose response streams the given chunks, optionally waiting for `gate` before the rest. */
function sseFetch(chunks: string[], gate?: Promise<void>) {
  return vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
    const signal = init?.signal
    const body = new ReadableStream<Uint8Array>({
      async start(controller) {
        const [first, ...rest] = chunks
        if (first) controller.enqueue(encoder.encode(first))
        if (gate) await gate
        if (signal?.aborted) return
        for (const chunk of rest) controller.enqueue(encoder.encode(chunk))
        controller.close()
      },
    })
    return new Response(body, { status: 200, headers: { "Content-Type": "text/event-stream" } })
  })
}

const frame = (event: AgentEvent) => `event: ${event.kind}\ndata: ${JSON.stringify(event)}\n\n`

describe("parseAgentEvent", () => {
  it("parses the backend payload and ignores junk", () => {
    expect(
      parseAgentEvent({
        event: "token",
        data: '{"agent":"assistant","kind":"token","message":"Hi"}',
      }),
    ).toEqual({
      agent: "assistant",
      kind: "token",
      message: "Hi",
      data: null,
    })
    expect(parseAgentEvent({ event: "", data: "not json" })).toBeNull()
    expect(parseAgentEvent({ event: "", data: '{"kind":"nope"}' })).toBeNull()
  })
})

describe("streamEvents", () => {
  it("delivers events across chunk boundaries and skips keep-alive comments", async () => {
    const started = frame({ agent: "travya", kind: "started", message: "Planning", data: null })
    const done = frame({ agent: "travya", kind: "done", message: "Ready", data: { trip_id: "t1" } })
    const fetchImpl = sseFetch([started.slice(0, 20), started.slice(20), ": ping\n\n", done])
    const events: AgentEvent[] = []
    await streamEvents("http://api.test/plan", {
      body: { instructions: null },
      signal: new AbortController().signal,
      fetch: fetchImpl,
      onEvent: (event) => events.push(event),
    })
    expect(events.map((event) => event.kind)).toEqual(["started", "done"])
    expect(events[1]?.data).toEqual({ trip_id: "t1" })
    const init = fetchImpl.mock.calls[0]?.[1]
    expect(init?.method).toBe("POST")
    expect(init?.body).toBe('{"instructions":null}')
  })

  it("rejects with an ApiError when the API refuses before streaming", async () => {
    const fetchImpl = vi.fn(
      async () =>
        new Response(JSON.stringify({ title: "Demo limit reached", detail: "Quota used." }), {
          status: 503,
          headers: { "Content-Type": "application/problem+json" },
        }),
    )
    const call = streamEvents("http://api.test/plan", {
      body: {},
      signal: new AbortController().signal,
      fetch: fetchImpl,
      onEvent: () => undefined,
    })
    await expect(call).rejects.toBeInstanceOf(ApiError)
    await expect(call).rejects.toMatchObject({ kind: "demo_limit", detail: "Quota used." })
    expect(fetchImpl).toHaveBeenCalledOnce() // never retried
  })

  it("stops delivering events once aborted", async () => {
    let release: () => void = () => undefined
    const gate = new Promise<void>((resolve) => {
      release = resolve
    })
    const fetchImpl = sseFetch(
      [
        frame({ agent: "assistant", kind: "token", message: "Hel", data: null }),
        frame({ agent: "assistant", kind: "token", message: "lo", data: null }),
      ],
      gate,
    )
    const controller = new AbortController()
    const events: AgentEvent[] = []
    const running = streamEvents("http://api.test/chat", {
      body: { content: "Hi" },
      signal: controller.signal,
      fetch: fetchImpl,
      onEvent: (event) => {
        events.push(event)
        controller.abort()
      },
    })
    await waitFor(() => expect(events).toHaveLength(1))
    release()
    await expect(running).resolves.toBeUndefined()
    expect(events.map((event) => event.message)).toEqual(["Hel"])
  })
})

describe("useEventStream", () => {
  it("reports streaming, then done", async () => {
    const fetchImpl = sseFetch([
      frame({ agent: "assistant", kind: "done", message: "", data: null }),
    ])
    const { result } = renderHook(() => useEventStream(fetchImpl))
    let outcome: unknown
    await act(async () => {
      outcome = await result.current.start("http://api.test/chat", {}, () => undefined)
    })
    expect(outcome).toBe("done")
    expect(result.current.status).toBe("done")
  })

  it("exposes the ApiError of a refused request", async () => {
    const fetchImpl = vi.fn(
      async () =>
        new Response(JSON.stringify({ title: "Too many requests", detail: "Slow down." }), {
          status: 429,
          headers: { "Retry-After": "30" },
        }),
    )
    const { result } = renderHook(() => useEventStream(fetchImpl))
    await act(async () => {
      await result.current.start("http://api.test/chat", {}, () => undefined)
    })
    expect(result.current.status).toBe("error")
    expect(result.current.error).toMatchObject({ status: 429, retryAfter: 30 })
  })
})
