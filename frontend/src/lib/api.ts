import { client } from "@/client/client.gen"
import { createAuthFetch } from "./authFetch"
import { configureClient } from "./clientConfig"
import { env } from "./env"
import { firebaseTokens } from "./firebase"

/** fetch with the Firebase ID token attached; shared by the generated client and the SSE streams. */
export const apiFetch = createAuthFetch(firebaseTokens)

export function apiUrl(path: string): string {
  return `${env.apiUrl}${path}`
}

let configured = false

export function setupApiClient(): void {
  if (configured) return
  configured = true
  configureClient(client, { baseUrl: env.apiUrl, fetch: apiFetch })
}
