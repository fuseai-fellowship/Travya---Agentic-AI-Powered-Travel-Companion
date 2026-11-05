import { useSyncExternalStore } from "react"

/** Set when the API answers 503 "Demo limit reached"; shown as a banner until dismissed. */
let message: string | null = null
const listeners = new Set<() => void>()

function emit() {
  for (const listener of listeners) listener()
}

export function reportDemoLimit(detail: string) {
  message = detail
  emit()
}

export function dismissDemoLimit() {
  message = null
  emit()
}

export function useDemoLimit(): string | null {
  return useSyncExternalStore(
    (listener) => {
      listeners.add(listener)
      return () => listeners.delete(listener)
    },
    () => message,
    () => null,
  )
}
