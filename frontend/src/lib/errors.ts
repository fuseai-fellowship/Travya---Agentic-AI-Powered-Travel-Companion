/** RFC 9457 problem+json responses from the API, normalised into one error type. */

export type ErrorKind =
  | "network"
  | "unauthorized"
  | "forbidden"
  | "not_found"
  | "conflict"
  | "validation"
  | "rate_limited"
  | "demo_limit"
  | "unavailable"
  | "server"
  | "unknown"

export interface FieldError {
  field: string
  message: string
}

interface ProblemBody {
  title?: unknown
  detail?: unknown
  errors?: unknown
}

const DEMO_LIMIT_TITLE = "Demo limit reached"

export class ApiError extends Error {
  readonly status: number
  readonly title: string
  readonly detail: string
  readonly retryAfter: number | null
  readonly fieldErrors: FieldError[]

  constructor(init: {
    status: number
    title: string
    detail: string
    retryAfter?: number | null
    fieldErrors?: FieldError[]
  }) {
    super(init.detail)
    this.name = "ApiError"
    this.status = init.status
    this.title = init.title
    this.detail = init.detail
    this.retryAfter = init.retryAfter ?? null
    this.fieldErrors = init.fieldErrors ?? []
  }

  get kind(): ErrorKind {
    const { status } = this
    if (status === 0) return "network"
    if (status === 401) return "unauthorized"
    if (status === 403) return "forbidden"
    if (status === 404) return "not_found"
    if (status === 409) return "conflict"
    if (status === 422 || status === 400) return "validation"
    if (status === 429) return "rate_limited"
    if (status === 503) return this.title === DEMO_LIMIT_TITLE ? "demo_limit" : "unavailable"
    if (status >= 500) return "server"
    return "unknown"
  }
}

/** Seconds from a Retry-After header (delta-seconds or an HTTP date). */
export function parseRetryAfter(value: string | null, now: number = Date.now()): number | null {
  if (!value) return null
  const seconds = Number(value)
  if (Number.isFinite(seconds)) return Math.max(0, Math.round(seconds))
  const date = Date.parse(value)
  if (Number.isNaN(date)) return null
  return Math.max(0, Math.round((date - now) / 1000))
}

function fieldErrors(errors: unknown): FieldError[] {
  if (!Array.isArray(errors)) return []
  return errors.flatMap((entry) => {
    if (typeof entry !== "object" || entry === null) return []
    const { loc, msg } = entry as { loc?: unknown; msg?: unknown }
    const path = Array.isArray(loc) ? loc.filter((part) => part !== "body" && part !== "query") : []
    return [{ field: path.join("."), message: typeof msg === "string" ? msg : "Invalid value" }]
  })
}

const FALLBACK_DETAIL: Record<number, string> = {
  0: "Can't reach the Travya server. Check your connection and try again.",
  401: "Your session has ended. Please sign in again.",
  403: "You don't have access to this.",
  404: "We couldn't find that. It may have been deleted.",
  429: "Too many requests. Please wait a moment.",
  500: "Something went wrong on our side.",
}

/** Builds an ApiError from whatever the client threw: a parsed body, raw text or a fetch failure. */
export function toApiError(body: unknown, response?: Response | null): ApiError {
  if (body instanceof ApiError) return body
  if (!response) {
    return new ApiError({ status: 0, title: "Network error", detail: FALLBACK_DETAIL[0] ?? "" })
  }
  const status = response.status
  const problem: ProblemBody = typeof body === "object" && body !== null ? body : {}
  const title =
    typeof problem.title === "string" ? problem.title : response.statusText || "Request failed"
  const rawDetail = typeof problem.detail === "string" ? problem.detail : null
  const errors = fieldErrors(
    problem.errors ?? (Array.isArray(problem.detail) ? problem.detail : []),
  )
  const detail =
    rawDetail && !(status === 422 && rawDetail === "Request validation failed" && errors.length)
      ? rawDetail
      : (errors[0]?.message ??
        FALLBACK_DETAIL[status] ??
        (status >= 500 ? FALLBACK_DETAIL[500] : "Request failed") ??
        "Request failed")
  return new ApiError({
    status,
    title,
    detail,
    retryAfter: parseRetryAfter(response.headers.get("Retry-After")),
    fieldErrors: errors,
  })
}

/** One human sentence for any error, suitable for a toast or an inline error state. */
export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.kind === "rate_limited" && error.retryAfter) {
      return `${error.detail.replace(/\.$/, "")}. Try again in ${formatWait(error.retryAfter)}.`
    }
    return error.detail
  }
  if (error instanceof Error && error.message) return error.message
  return "Something went wrong. Please try again."
}

export function formatWait(seconds: number): string {
  if (seconds < 60) return `${seconds} s`
  const minutes = Math.ceil(seconds / 60)
  return minutes === 1 ? "1 minute" : `${minutes} minutes`
}
