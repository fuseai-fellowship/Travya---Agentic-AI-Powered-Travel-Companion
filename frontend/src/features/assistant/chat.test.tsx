import { act, screen, waitFor, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { HttpResponse, http } from "msw"
import { beforeAll, describe, expect, it, vi } from "vitest"
import { setupApiClient } from "@/lib/api"
import { page } from "@/test/fixtures"
import { renderWithClient } from "@/test/render"
import { server } from "@/test/server"
import { deferred, frame, SSE_HEADERS, sseBody } from "@/test/sse"
import { PendingReply, SLOW_AFTER_MS } from "./PendingReply"
import { Thread } from "./Thread"
import { type PendingTurn, speakable, useChat } from "./useChat"

vi.mock("@/lib/firebase", async () => (await import("@/test/sse")).firebaseMock)

beforeAll(() => setupApiClient())

const API = "http://localhost:8000/api/v1"
const CONV = "conv-1"
const QUESTION = "Will it rain on day 3?"

interface Stored {
  id: string
  role: "user" | "assistant"
  content: string
  meta: Record<string, unknown>
  created_at: string
}

/**
 * A conversation whose API behaves like the backend: it saves the user's message when the stream
 * opens, and doesn't save it again when an unanswered question is resent.
 */
function api(reply: (posts: number, signal: AbortSignal, stored: Stored[]) => Response) {
  const stored: Stored[] = []
  let posts = 0
  server.use(
    http.get(`${API}/conversations/:id/messages`, () => HttpResponse.json(page(stored))),
    http.get(`${API}/conversations`, () => HttpResponse.json(page([]))),
    http.post(`${API}/conversations/:id/messages`, async ({ request }) => {
      posts += 1
      const { content } = (await request.json()) as { content: string }
      const response = reply(posts, request.signal, stored)
      const last = stored.at(-1)
      const resent = last?.role === "user" && last.content === content
      if (response.headers.get("content-type")?.includes("event-stream") && !resent) {
        stored.push({
          id: `u${posts}`,
          role: "user",
          content,
          meta: {},
          created_at: "2026-11-06T10:00:00Z",
        })
      }
      return response
    }),
  )
  return { stored, posts: () => posts }
}

function Chat() {
  const chat = useChat()
  return (
    <Thread
      conversationId={CONV}
      pending={chat.pending}
      announcement={chat.announcement}
      onSend={(content) => void chat.send(CONV, content)}
      onStop={chat.stop}
    />
  )
}

async function ask(text = QUESTION) {
  const user = userEvent.setup()
  const box = await screen.findByRole("textbox", { name: "Message the travel assistant" })
  await user.type(box, `${text}{Enter}`)
  return user
}

describe("assistant thread", () => {
  it("shows a working indicator with tool steps, then announces the finished reply", async () => {
    const release = deferred()
    const { stored } = api(
      () =>
        new HttpResponse(
          sseBody(
            [
              frame({ agent: "assistant", kind: "progress", message: "Looking at your trips…" }),
              frame({ agent: "assistant", kind: "progress", message: "Looking at your trips…" }),
            ],
            [
              frame({ agent: "assistant", kind: "token", message: "No rain is **expected**." }),
              frame({ agent: "assistant", kind: "done" }),
            ],
            release.promise,
          ),
          { headers: SSE_HEADERS },
        ),
    )
    renderWithClient(<Chat />)
    await ask()

    const log = await screen.findByRole("log", { name: "Conversation" })
    expect(log).toHaveAttribute("aria-live", "off")
    // The step list (deduplicated) and the status line next to the typing dots.
    expect(await within(log).findAllByText("Looking at your trips…")).toHaveLength(2)
    expect(within(log).getByTestId("typing")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /Stop/ })).toBeEnabled()

    stored.push({
      id: "a1",
      role: "assistant",
      content: "No rain is **expected**.",
      meta: { tools: ["my_trips"] },
      created_at: "2026-11-06T10:00:09Z",
    })
    act(() => release.resolve())

    await waitFor(() =>
      expect(screen.getByRole("status")).toHaveTextContent("Travya replied: No rain is expected."),
    )
    expect(within(log).getAllByText(QUESTION)).toHaveLength(1)
    expect(within(log).queryByTestId("typing")).not.toBeInTheDocument()
    expect(screen.getByRole("button", { name: /Send/ })).toBeInTheDocument()
  })

  it("renders the question once after a backend error and retries it", async () => {
    const hold = deferred()
    const { posts } = api((count) =>
      count === 1
        ? new HttpResponse(
            sseBody([
              frame({ agent: "assistant", kind: "progress", message: "Checking the weather…" }),
              frame({
                agent: "assistant",
                kind: "error",
                message: "The assistant is unavailable right now. Please try again in a moment.",
              }),
            ]),
            { headers: SSE_HEADERS },
          )
        : new HttpResponse(sseBody([": ping\n\n"], [], hold.promise), { headers: SSE_HEADERS }),
    )
    renderWithClient(<Chat />)
    const user = await ask()

    const alert = await screen.findByRole("alert")
    expect(alert).toHaveTextContent("The assistant is unavailable right now")
    const log = screen.getByRole("log", { name: "Conversation" })
    await waitFor(() => expect(within(log).getAllByText(QUESTION)).toHaveLength(1))
    // No empty or "…" assistant bubble is left behind.
    expect(within(log).queryByTestId("typing")).not.toBeInTheDocument()
    expect(within(log).queryByText("…")).not.toBeInTheDocument()

    await user.click(within(alert).getByRole("button", { name: "Retry" }))
    await waitFor(() => expect(posts()).toBe(2))
    // While the retry runs, the stored question is still shown once.
    expect(await within(log).findByTestId("typing")).toBeInTheDocument()
    expect(within(log).getAllByText(QUESTION)).toHaveLength(1)
    act(() => hold.resolve())
  })

  it("shows the partial reply the API kept, once, marked as interrupted", async () => {
    api(
      (_count, _signal, stored) =>
        new HttpResponse(
          sseBody(
            [frame({ agent: "assistant", kind: "token", message: "Day 3 looks dry, but" })],
            [frame({ agent: "assistant", kind: "error", message: "The assistant timed out." })],
            // The server stores the partial reply before it reports the error.
            Promise.resolve().then(() => {
              stored.push({
                id: "a-partial",
                role: "assistant",
                content: "Day 3 looks dry, but",
                meta: { interrupted: true },
                created_at: "2026-11-06T10:00:30Z",
              })
            }),
          ),
          { headers: SSE_HEADERS },
        ),
    )
    renderWithClient(<Chat />)
    await ask()
    expect(await screen.findByRole("alert")).toHaveTextContent("The assistant timed out.")
    const log = screen.getByRole("log", { name: "Conversation" })
    await waitFor(() => expect(within(log).getAllByText("Day 3 looks dry, but")).toHaveLength(1))
    expect(within(log).getByText("Interrupted before it finished")).toBeInTheDocument()
  })

  it("keeps an unsent message with the API's reason and a retry", async () => {
    api(() =>
      HttpResponse.json(
        { title: "Too many requests", detail: "Rate limit reached (20/hour)." },
        { status: 429, headers: { "Content-Type": "application/problem+json" } },
      ),
    )
    renderWithClient(<Chat />)
    await ask()
    const alert = await screen.findByRole("alert")
    expect(alert).toHaveTextContent("Rate limit reached (20/hour).")
    const log = screen.getByRole("log", { name: "Conversation" })
    expect(within(log).getAllByText(QUESTION)).toHaveLength(1)
    expect(within(alert).getByRole("button", { name: "Retry" })).toBeInTheDocument()
  })

  it("stops a slow reply for real", async () => {
    const aborted = vi.fn()
    const never = deferred()
    api((_posts, signal) => {
      signal.addEventListener("abort", aborted)
      return new HttpResponse(sseBody([": ping\n\n"], [], never.promise), {
        headers: SSE_HEADERS,
      })
    })
    renderWithClient(<Chat />)
    const user = await ask()
    await screen.findByText("Thinking…")
    await user.click(screen.getByRole("button", { name: /Stop/ }))

    expect(await screen.findByText("Stopped before a reply.")).toBeInTheDocument()
    await waitFor(() => expect(aborted).toHaveBeenCalled())
    expect(screen.getByRole("status")).toHaveTextContent("Stopped.")
    expect(screen.getByRole("button", { name: /Send/ })).toBeInTheDocument()
  })
})

describe("PendingReply", () => {
  const turn = (change: Partial<PendingTurn>): PendingTurn => ({
    conversationId: CONV,
    user: QUESTION,
    reply: "",
    tools: [],
    phase: "waiting",
    startedAt: Date.now(),
    error: null,
    saved: true,
    ...change,
  })

  it("explains a slow free-tier model after a while", () => {
    const { unmount } = renderWithClient(<PendingReply turn={turn({})} />)
    expect(screen.queryByText(/Still working/)).not.toBeInTheDocument()
    unmount()
    renderWithClient(<PendingReply turn={turn({ startedAt: Date.now() - SLOW_AFTER_MS - 500 })} />)
    expect(screen.getByText(/Still working. The free-tier model can take about 30/)).toBeVisible()
    expect(screen.getByText(/^1\d\.\d|^1\d\s/)).toBeInTheDocument() // the elapsed timer
  })

  it("renders nothing for a failed turn without text", () => {
    const { container } = renderWithClient(
      <PendingReply turn={turn({ phase: "error", error: "x" })} />,
    )
    expect(container).toBeEmptyDOMElement()
  })
})

describe("Composer while the conversation is created", () => {
  it("says Sending instead of offering a Stop that does nothing", async () => {
    api(() => new HttpResponse(null, { status: 500 }))
    renderWithClient(
      <Thread conversationId={CONV} pending={null} creating onSend={vi.fn()} onStop={vi.fn()} />,
    )
    expect(await screen.findByRole("button", { name: "Sending…" })).toBeDisabled()
    expect(screen.queryByRole("button", { name: /Stop/ })).not.toBeInTheDocument()
  })
})

describe("long threads", () => {
  it("shows the latest page of messages", async () => {
    const all = Array.from({ length: 205 }, (_, index) => ({
      id: `m${index}`,
      role: "user" as const,
      content: `Message ${index}`,
      meta: {},
      created_at: "2026-11-06T10:00:00Z",
    }))
    server.use(
      http.get(`${API}/conversations/:id/messages`, ({ request }) => {
        const url = new URL(request.url)
        const offset = Number(url.searchParams.get("offset") ?? 0)
        const limit = Number(url.searchParams.get("limit") ?? 100)
        return HttpResponse.json({
          items: all.slice(offset, offset + limit),
          total: all.length,
          limit,
          offset,
        })
      }),
    )
    renderWithClient(
      <Thread conversationId={CONV} pending={null} onSend={vi.fn()} onStop={vi.fn()} />,
    )
    expect(await screen.findByText("Message 204")).toBeInTheDocument()
    expect(screen.queryByText("Message 0")).not.toBeInTheDocument()
    expect(screen.getByText("Showing the latest 200 messages.")).toBeInTheDocument()
  })
})

describe("speakable", () => {
  it("strips Markdown for the announcement", () => {
    expect(speakable("**Day 3**: see [Open-Meteo](https://open-meteo.com)\n\n- `dry`")).toBe(
      "Day 3: see Open-Meteo - dry",
    )
  })
})
