export interface TokenSource {
  /** The current ID token, refreshed when `forceRefresh` is set; null when signed out. */
  getToken(forceRefresh: boolean): Promise<string | null>
  /** Called when the API still answers 401 after one refresh. */
  onUnauthorized(): void
}

function withToken(request: Request, token: string | null): Request {
  if (!token) return request
  const headers = new Headers(request.headers)
  headers.set("Authorization", `Bearer ${token}`)
  return new Request(request, { headers })
}

/**
 * A fetch that attaches the Firebase ID token, retries once with a fresh token on 401,
 * and reports a second 401 so the app can sign out.
 */
export function createAuthFetch(
  source: TokenSource,
  baseFetch: typeof fetch = (input, init) => globalThis.fetch(input, init),
): typeof fetch {
  return async (input, init) => {
    const request = new Request(input, init)
    const spare = request.clone()
    const token = await source.getToken(false)
    const first = await baseFetch(withToken(request, token))
    if (first.status !== 401 || !token) return first

    const fresh = await source.getToken(true).catch(() => null)
    if (!fresh) {
      source.onUnauthorized()
      return first
    }
    const second = await baseFetch(withToken(spare, fresh))
    if (second.status === 401) source.onUnauthorized()
    return second
  }
}
