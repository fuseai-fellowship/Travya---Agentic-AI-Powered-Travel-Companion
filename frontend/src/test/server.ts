import { HttpResponse, http } from "msw"
import { setupServer } from "msw/node"

export const API = "http://api.test"

/**
 * Tests add their own handlers with `server.use(...)`; unmatched requests fail the test. The API's
 * health check always answers, so the cold-start wake-up (`lib/wake.ts`) never waits in tests.
 */
export const server = setupServer(
  http.get("*/api/v1/health/live", () => HttpResponse.json({ status: "ok" })),
)
