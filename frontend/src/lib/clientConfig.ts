import type { Client } from "@/client/client"
import { toApiError } from "./errors"

/** Points a generated client at the API and turns every failure into an ApiError. */
export function configureClient(client: Client, options: { baseUrl: string; fetch: typeof fetch }) {
  client.setConfig({ baseUrl: options.baseUrl, fetch: options.fetch, throwOnError: true })
  client.interceptors.error.use((error, response) => toApiError(error, response))
}
