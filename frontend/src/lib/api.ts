import { client } from "@/client/client.gen"
import { createAuthFetch } from "./authFetch"
import { configureClient } from "./clientConfig"
import { env } from "./env"
import { firebaseTokens } from "./firebase"
import { wakeServer, withWakeUp } from "./wake"

export function apiUrl(path: string): string {
  return `${env.apiUrl}${path}`
}

export const HEALTH_URL = apiUrl("/api/v1/health/live")

/** Starts waking the free API server (or finds it awake); one poll loop at a time. */
export const wakeApi = () => wakeServer({ healthUrl: HEALTH_URL })

/**
 * fetch with the Firebase ID token attached that also rides out a sleeping server; shared by the
 * generated client and the SSE streams.
 */
export const apiFetch = createAuthFetch(
  firebaseTokens,
  withWakeUp((input, init) => globalThis.fetch(input, init), wakeApi),
)

let configured = false

export function setupApiClient(): void {
  if (configured) return
  configured = true
  configureClient(client, { baseUrl: env.apiUrl, fetch: apiFetch })
}
