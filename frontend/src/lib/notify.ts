import { toaster } from "@/components/ui/toaster"
import { reportDemoLimit } from "./demoLimit"
import { ApiError, errorMessage } from "./errors"
import { WOKE_TITLE } from "./wake"

const TITLES: Partial<Record<ApiError["kind"], string>> = {
  network: "You're offline",
  rate_limited: "Slow down a little",
  demo_limit: "Demo limit reached",
  unavailable: "Service unavailable",
  validation: "Check the form",
  conflict: "Already changed",
  not_found: "Not found",
  forbidden: "Not allowed",
  server: "Something went wrong",
}

/** Shows an API or app error as a toast; the demo limit also raises the global banner. */
export function notifyError(error: unknown, fallbackTitle = "That didn't work") {
  if (error instanceof ApiError) {
    if (error.kind === "unauthorized") return // the session handler explains and redirects
    if (error.kind === "demo_limit") reportDemoLimit(error.detail)
  }
  const title =
    error instanceof ApiError
      ? error.title === WOKE_TITLE
        ? WOKE_TITLE
        : (TITLES[error.kind] ?? fallbackTitle)
      : fallbackTitle
  toaster.create({
    type: "error",
    title,
    description: errorMessage(error),
    duration: error instanceof ApiError && error.kind === "rate_limited" ? 8000 : 6000,
  })
}

export function notifySuccess(title: string, description?: string) {
  toaster.create({ type: "success", title, description, duration: 4000 })
}
