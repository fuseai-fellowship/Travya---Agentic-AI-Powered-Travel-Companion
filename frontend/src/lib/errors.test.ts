import { HttpResponse, http } from "msw"
import { beforeEach, describe, expect, it } from "vitest"
import { createClient, createConfig } from "@/client/client"
import { tripsGetTrip, tripsListTrips } from "@/client/sdk.gen"
import { API, server } from "@/test/server"
import { configureClient } from "./clientConfig"
import { ApiError, errorMessage, parseRetryAfter, toApiError } from "./errors"

const problem = (status: number, title: string, detail: string, init: ResponseInit = {}) =>
  HttpResponse.json(
    { type: "about:blank", title, status, detail, instance: "/x" },
    { status, headers: { "Content-Type": "application/problem+json", ...init.headers } },
  )

describe("toApiError", () => {
  it("reads problem+json title, detail and Retry-After", () => {
    const response = new Response(null, { status: 429, headers: { "Retry-After": "42" } })
    const error = toApiError(
      { title: "Too many requests", detail: "Rate limit reached (6/hour)." },
      response,
    )
    expect(error.kind).toBe("rate_limited")
    expect(error.retryAfter).toBe(42)
    expect(errorMessage(error)).toBe("Rate limit reached (6/hour). Try again in 42 s.")
  })

  it("tells the demo limit apart from other 503s", () => {
    const demo = toApiError(
      { title: "Demo limit reached", detail: "Quota used." },
      new Response(null, { status: 503 }),
    )
    const upstream = toApiError(
      { title: "Upstream service unavailable", detail: "Weather is down." },
      new Response(null, { status: 503 }),
    )
    expect(demo.kind).toBe("demo_limit")
    expect(upstream.kind).toBe("unavailable")
  })

  it("surfaces the first field error of a request validation failure", () => {
    const error = toApiError(
      {
        title: "Invalid input",
        detail: "Request validation failed",
        errors: [
          {
            loc: ["body", "end_date"],
            msg: "Value error, Trips can be at most 21 days",
            type: "value_error",
          },
        ],
      },
      new Response(null, { status: 422 }),
    )
    expect(error.kind).toBe("validation")
    expect(error.detail).toBe("Value error, Trips can be at most 21 days")
    expect(error.fieldErrors).toEqual([
      { field: "end_date", message: "Value error, Trips can be at most 21 days" },
    ])
  })

  it("maps a failed fetch to a network error", () => {
    const error = toApiError(new TypeError("Failed to fetch"), undefined)
    expect(error.kind).toBe("network")
    expect(error.status).toBe(0)
  })

  it("parses HTTP-date Retry-After values", () => {
    const now = Date.parse("2026-11-05T10:00:00Z")
    expect(parseRetryAfter("Thu, 05 Nov 2026 10:01:30 GMT", now)).toBe(90)
    expect(parseRetryAfter(null)).toBeNull()
  })
})

describe("generated client error mapping", () => {
  const client = createClient(createConfig())

  beforeEach(() =>
    configureClient(client, { baseUrl: API, fetch: (input, init) => fetch(input, init) }),
  )

  it("throws ApiError with the server's detail", async () => {
    server.use(
      http.get(`${API}/api/v1/trips/:id`, () => problem(404, "Not found", "Trip not found")),
    )
    const call = tripsGetTrip({ client, path: { trip_id: "00000000-0000-0000-0000-000000000000" } })
    await expect(call).rejects.toBeInstanceOf(ApiError)
    await expect(call).rejects.toMatchObject({
      status: 404,
      detail: "Trip not found",
      kind: "not_found",
    })
  })

  it("keeps Retry-After from a 429", async () => {
    server.use(
      http.get(`${API}/api/v1/trips`, () =>
        problem(429, "Too many requests", "Rate limit reached (120/minute). Try again later.", {
          headers: { "Retry-After": "7" },
        }),
      ),
    )
    await expect(tripsListTrips({ client })).rejects.toMatchObject({ status: 429, retryAfter: 7 })
  })

  it("returns parsed data on success", async () => {
    server.use(
      http.get(`${API}/api/v1/trips`, () =>
        HttpResponse.json({ items: [], total: 0, limit: 20, offset: 0 }),
      ),
    )
    const { data } = await tripsListTrips({ client, throwOnError: true })
    expect(data.total).toBe(0)
  })
})
