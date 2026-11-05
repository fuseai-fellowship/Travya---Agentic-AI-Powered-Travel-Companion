import { describe, expect, it, vi } from "vitest"
import { createAuthFetch, type TokenSource } from "./authFetch"

function source(tokens: Array<string | null>) {
  const getToken = vi.fn(async (_force: boolean) => tokens.shift() ?? null)
  const onUnauthorized = vi.fn()
  return { getToken, onUnauthorized } satisfies TokenSource
}

const respond = (...statuses: number[]) => {
  const seen: Array<string | null> = []
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const request = input as Request
    seen.push(request.headers.get("Authorization"))
    return new Response(null, { status: statuses.shift() ?? 200 })
  })
  return { fetchMock, seen }
}

describe("createAuthFetch", () => {
  it("attaches the ID token", async () => {
    const tokens = source(["token-1"])
    const { fetchMock, seen } = respond(200)
    const response = await createAuthFetch(tokens, fetchMock)("http://api.test/api/v1/me")
    expect(response.status).toBe(200)
    expect(seen).toEqual(["Bearer token-1"])
    expect(tokens.getToken).toHaveBeenCalledWith(false)
  })

  it("refreshes the token once after a 401 and replays the request body", async () => {
    const tokens = source(["stale", "fresh"])
    const bodies: string[] = []
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const request = input as Request
      bodies.push(await request.text())
      return new Response(null, {
        status: request.headers.get("Authorization") === "Bearer fresh" ? 200 : 401,
      })
    })
    const response = await createAuthFetch(tokens, fetchMock)("http://api.test/api/v1/notes", {
      method: "POST",
      body: JSON.stringify({ title: "Hi" }),
    })
    expect(response.status).toBe(200)
    expect(tokens.getToken).toHaveBeenLastCalledWith(true)
    expect(bodies).toEqual(['{"title":"Hi"}', '{"title":"Hi"}'])
    expect(tokens.onUnauthorized).not.toHaveBeenCalled()
  })

  it("signs out when the refreshed token is rejected too", async () => {
    const tokens = source(["stale", "fresh"])
    const { fetchMock } = respond(401, 401)
    const response = await createAuthFetch(tokens, fetchMock)("http://api.test/api/v1/me")
    expect(response.status).toBe(401)
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(tokens.onUnauthorized).toHaveBeenCalledOnce()
  })

  it("does not retry anonymous requests", async () => {
    const tokens = source([null])
    const { fetchMock, seen } = respond(401)
    await createAuthFetch(tokens, fetchMock)("http://api.test/api/v1/me")
    expect(seen).toEqual([null])
    expect(fetchMock).toHaveBeenCalledOnce()
  })
})
