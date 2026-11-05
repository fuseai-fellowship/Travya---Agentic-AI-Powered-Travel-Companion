import { act, renderHook, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { HttpResponse, http } from "msw"
import { afterEach, beforeAll, describe, expect, it, vi } from "vitest"
import { setupApiClient } from "@/lib/api"
import type { AgentEvent } from "@/lib/sse"
import { renderWithClient } from "@/test/render"
import { server } from "@/test/server"
import { deferred, frame, SSE_HEADERS, sseBody } from "@/test/sse"
import { PlanningPanel } from "./PlanningPanel"
import { ANNOUNCE_EVERY_MS, useThrottledText } from "./ProgressAnnouncer"
import {
  dismissPlan,
  retryPlan,
  STOPPED_MESSAGE,
  startPlan,
  stopPlan,
  usePlanRun,
} from "./planStore"

vi.mock("@/lib/firebase", async () => (await import("@/test/sse")).firebaseMock)
vi.mock("@/lib/notify", () => ({ notifyError: vi.fn(), notifySuccess: vi.fn() }))

beforeAll(() => setupApiClient())

const API = "http://localhost:8000/api/v1"
let tripCounter = 0
const nextTrip = () => `trip-${++tripCounter}`

afterEach(() => {
  for (let index = 1; index <= tripCounter; index += 1) {
    stopPlan(`trip-${index}`)
    dismissPlan(`trip-${index}`)
  }
})

const ev = (event: Partial<AgentEvent> & Pick<AgentEvent, "kind">) => frame(event)

function Panel({ tripId, onRetry = vi.fn() }: { tripId: string; onRetry?: () => void }) {
  const run = usePlanRun(tripId)
  return (
    <PlanningPanel
      tripId={tripId}
      run={run}
      planningElsewhere={false}
      onRetry={onRetry}
      onStop={() => stopPlan(tripId)}
    />
  )
}

function planApi(
  respond: (body: { instructions: string | null }, signal: AbortSignal) => Response,
) {
  const bodies: Array<{ instructions: string | null }> = []
  server.use(
    http.get(`${API}/trips/:id`, () => HttpResponse.json({})),
    http.get(`${API}/trips/:id/*`, () => HttpResponse.json([])),
    http.post(`${API}/trips/:id/plan`, async ({ request }) => {
      const body = (await request.json()) as { instructions: string | null }
      bodies.push(body)
      return respond(body, request.signal)
    }),
  )
  return bodies
}

describe("planning panel", () => {
  it("announces progress politely and keeps the live region across the done transition", async () => {
    const release = deferred()
    planApi(
      () =>
        new HttpResponse(
          sseBody(
            [
              ev({ kind: "started", message: "Planning your trip to Kyoto" }),
              ev({ agent: "planner", kind: "started" }),
              ev({
                agent: "planner",
                kind: "result",
                message: "Drafted 2 days with 6 activities.",
              }),
              ev({ agent: "finalize", kind: "started", message: "finalize started" }),
            ],
            [
              ev({
                kind: "done",
                message: "Your 2-day itinerary is ready.",
                data: { trip_id: "t" },
              }),
            ],
            release.promise,
          ),
          { headers: SSE_HEADERS },
        ),
    )
    const tripId = nextTrip()
    const { queryClient } = renderWithClient(<Panel tripId={tripId} />)
    act(() => startPlan(queryClient, tripId))

    const region = await screen.findByRole("status")
    expect(region).toHaveAttribute("aria-live", "polite")
    await waitFor(() => expect(region).toHaveTextContent("Placing stops on the map."), {
      timeout: ANNOUNCE_EVERY_MS + 2000,
    })
    expect(screen.getByText("Map")).toBeInTheDocument()

    act(() => release.resolve())
    await waitFor(() => expect(region).toHaveTextContent("Your 2-day itinerary is ready."))
    expect(screen.getByRole("status")).toBe(region) // same node: never unmounted
  }, 15_000)

  it("stops a run for real and retries with the original instructions", async () => {
    const aborted = vi.fn()
    const bodies = planApi((_body, signal) => {
      signal.addEventListener("abort", aborted)
      return new HttpResponse(
        sseBody([ev({ kind: "started", message: "Planning" })], [], new Promise(() => undefined)),
        {
          headers: SSE_HEADERS,
        },
      )
    })
    const tripId = nextTrip()
    const user = userEvent.setup()
    const { queryClient } = renderWithClient(
      <Panel tripId={tripId} onRetry={() => retryPlan(queryClient, tripId)} />,
    )
    act(() => startPlan(queryClient, tripId, "  vegetarian, slow mornings "))
    await user.click(await screen.findByRole("button", { name: "Stop" }))
    expect(await screen.findByText(STOPPED_MESSAGE)).toBeInTheDocument()
    await waitFor(() => expect(aborted).toHaveBeenCalled())

    await user.click(screen.getByRole("button", { name: "Try again" }))
    await waitFor(() => expect(bodies).toHaveLength(2))
    expect(bodies.map((body) => body.instructions)).toEqual([
      "vegetarian, slow mornings",
      "vegetarian, slow mornings",
    ])
  })

  it("reports a stream that ends before the plan is ready", async () => {
    planApi(
      () =>
        new HttpResponse(sseBody([ev({ kind: "started", message: "Planning" })]), {
          headers: SSE_HEADERS,
        }),
    )
    const tripId = nextTrip()
    const { queryClient } = renderWithClient(<Panel tripId={tripId} />)
    act(() => startPlan(queryClient, tripId))
    expect(
      await screen.findByText("The planning stream ended early. Please re-plan."),
    ).toBeVisible()
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument()
  })

  it("shows the API's reason when it refuses to start", async () => {
    planApi(() =>
      HttpResponse.json(
        { title: "Demo limit reached", detail: "Today's demo budget is used up." },
        { status: 503, headers: { "Content-Type": "application/problem+json" } },
      ),
    )
    const tripId = nextTrip()
    const { queryClient } = renderWithClient(<Panel tripId={tripId} />)
    act(() => startPlan(queryClient, tripId))
    expect(await screen.findByText("Today's demo budget is used up.")).toBeVisible()
  })
})

describe("useThrottledText", () => {
  it("speaks at most once per interval but never delays the final message", () => {
    vi.useFakeTimers()
    try {
      const { result, rerender } = renderHook(
        ({ text, flush }: { text: string; flush: boolean }) => useThrottledText(text, 4000, flush),
        { initialProps: { text: "1 of 4 research scouts done.", flush: false } },
      )
      act(() => vi.advanceTimersByTime(1))
      expect(result.current).toBe("1 of 4 research scouts done.")

      rerender({ text: "2 of 4 research scouts done.", flush: false })
      act(() => vi.advanceTimersByTime(1000))
      expect(result.current).toBe("1 of 4 research scouts done.")
      act(() => vi.advanceTimersByTime(3100))
      expect(result.current).toBe("2 of 4 research scouts done.")

      rerender({ text: "Your 3-day itinerary is ready.", flush: true })
      act(() => vi.advanceTimersByTime(1))
      expect(result.current).toBe("Your 3-day itinerary is ready.")
    } finally {
      vi.useRealTimers()
    }
  })
})

function RunProbe({ tripId }: { tripId: string }) {
  const run = usePlanRun(tripId)
  return <p>{run ? `run ${run.state.status}` : "no run"}</p>
}

describe("planning conflicts and budget", () => {
  it("follows a run already going elsewhere instead of failing", async () => {
    planApi(() =>
      HttpResponse.json(
        { title: "Conflict", detail: "This trip is already being planned." },
        { status: 409, headers: { "Content-Type": "application/problem+json" } },
      ),
    )
    const tripId = nextTrip()
    const { queryClient } = renderWithClient(<RunProbe tripId={tripId} />)
    act(() => startPlan(queryClient, tripId))
    expect(screen.getByText("run running")).toBeInTheDocument()
    expect(await screen.findByText("no run")).toBeInTheDocument()
  })

  it("raises the demo-limit banner when the run's budget runs out", async () => {
    const demoLimit = await import("@/lib/demoLimit")
    const report = vi.spyOn(demoLimit, "reportDemoLimit")
    planApi(
      () =>
        new HttpResponse(
          sseBody([
            ev({ kind: "started", message: "Planning" }),
            ev({
              kind: "error",
              message: "Today's demo budget is used up.",
              data: { error: "BudgetExhausted" },
            }),
          ]),
          { headers: SSE_HEADERS },
        ),
    )
    const tripId = nextTrip()
    const { queryClient } = renderWithClient(<Panel tripId={tripId} />)
    act(() => startPlan(queryClient, tripId))
    expect(await screen.findAllByText("Today's demo budget is used up.")).not.toHaveLength(0)
    expect(report).toHaveBeenCalledWith("Today's demo budget is used up.")
  })
})
