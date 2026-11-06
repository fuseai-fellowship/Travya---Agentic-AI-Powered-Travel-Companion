import { afterEach, describe, expect, it, vi } from "vitest"
import { ApiError } from "./errors"
import { resetWake, WOKE_TITLE, wakeServer, wakeStatus, warmServer, withWakeUp } from "./wake"

const HEALTH = "http://api.test/api/v1/health/live"

afterEach(() => resetWake())

/** A health endpoint that is down for the first `downFor` polls, then live. */
function health(downFor: number) {
  let calls = 0
  const fetchImpl = vi.fn(async () => {
    calls += 1
    if (calls <= downFor) throw new TypeError("Failed to fetch")
    return new Response('{"status":"ok"}', { status: 200 })
  })
  return { fetchImpl, calls: () => calls }
}

describe("wakeServer", () => {
  it("polls with back-off until the server answers, once for many callers", async () => {
    const { fetchImpl } = health(3)
    const sleeps: number[] = []
    const options = {
      healthUrl: HEALTH,
      fetch: fetchImpl as unknown as typeof fetch,
      sleep: async (ms: number) => void sleeps.push(ms),
    }
    const [a, b] = await Promise.all([wakeServer(options), wakeServer(options)])
    expect([a, b]).toEqual([true, true])
    expect(fetchImpl).toHaveBeenCalledTimes(4)
    expect(sleeps).toEqual([1000, 2000, 3000])
    expect(wakeStatus()).toBe("awake")
  })

  it("gives up after the timeout", async () => {
    let clock = 0
    const fetchImpl = vi.fn(async () => new Response("asleep", { status: 503 }))
    const awake = await wakeServer({
      healthUrl: HEALTH,
      fetch: fetchImpl as unknown as typeof fetch,
      timeoutMs: 20_000,
      delaysMs: [5000],
      now: () => clock,
      sleep: async (ms) => {
        clock += ms
      },
    })
    expect(awake).toBe(false)
    expect(wakeStatus()).toBe("failed")
    expect(fetchImpl).toHaveBeenCalledTimes(5)
  })
})

describe("withWakeUp", () => {
  it("waits for a sleeping server and retries a read", async () => {
    const base = vi
      .fn<typeof fetch>()
      .mockRejectedValueOnce(new TypeError("Failed to fetch"))
      .mockResolvedValueOnce(Response.json({ items: [] }))
    const wake = vi.fn(async () => true)
    const response = await withWakeUp(base, wake)("http://api.test/api/v1/trips")
    expect(wake).toHaveBeenCalledOnce()
    expect(base).toHaveBeenCalledTimes(2)
    expect(await response.json()).toEqual({ items: [] })
  })

  it("treats the Space's HTML 503 page as asleep", async () => {
    const base = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(
        new Response("<html>Space is sleeping</html>", {
          status: 503,
          headers: { "Content-Type": "text/html" },
        }),
      )
      .mockResolvedValueOnce(Response.json({ ok: true }))
    const wake = vi.fn(async () => true)
    const response = await withWakeUp(base, wake)("http://api.test/api/v1/me")
    expect(response.status).toBe(200)
    // A JSON 503 is the API itself answering (e.g. the demo limit): passed through untouched.
    const demoLimit = Response.json({ title: "Demo limit reached" }, { status: 503 })
    const passthrough = await withWakeUp(
      vi.fn(async () => demoLimit),
      wake,
    )("http://api.test/x")
    expect(passthrough).toBe(demoLimit)
    expect(wake).toHaveBeenCalledOnce()
  })

  it("never replays a write; it asks the user to try again", async () => {
    const base = vi.fn<typeof fetch>().mockRejectedValue(new TypeError("Failed to fetch"))
    const call = withWakeUp(base, async () => true)("http://api.test/api/v1/trips/1/plan", {
      method: "POST",
      body: "{}",
    })
    await expect(call).rejects.toBeInstanceOf(ApiError)
    await expect(call).rejects.toMatchObject({ title: WOKE_TITLE, kind: "network" })
    expect(base).toHaveBeenCalledOnce()
  })

  it("passes aborts and dead servers through", async () => {
    const abort = new DOMException("aborted", "AbortError")
    const wake = vi.fn(async () => false)
    await expect(
      withWakeUp(vi.fn<typeof fetch>().mockRejectedValue(abort), wake)("http://api.test/a"),
    ).rejects.toBe(abort)
    expect(wake).not.toHaveBeenCalled()
    const offline = new TypeError("Failed to fetch")
    await expect(
      withWakeUp(vi.fn<typeof fetch>().mockRejectedValue(offline), wake)("http://api.test/a"),
    ).rejects.toBe(offline)
  })
})

describe("warmServer", () => {
  it("fires one request and swallows failures", async () => {
    const fetchImpl = vi.fn<typeof fetch>().mockRejectedValue(new TypeError("offline"))
    warmServer(HEALTH, fetchImpl)
    expect(fetchImpl).toHaveBeenCalledWith(HEALTH, expect.objectContaining({ keepalive: true }))
  })
})
