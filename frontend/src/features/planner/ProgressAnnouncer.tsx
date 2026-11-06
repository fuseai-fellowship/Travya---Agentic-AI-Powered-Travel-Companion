import { Text } from "@chakra-ui/react"
import { useEffect, useRef, useState } from "react"
import { describeProgress, type TimelineState } from "./timeline"

/** Minimum gap between two announcements while a plan runs; the final one is never delayed. */
export const ANNOUNCE_EVERY_MS = 4000

/** Follows `text`, but changes at most once per `intervalMs` unless `flush` is set. */
export function useThrottledText(text: string, intervalMs: number, flush: boolean): string {
  const [spoken, setSpoken] = useState("")
  const lastAt = useRef(0)
  useEffect(() => {
    if (text === spoken) return
    const wait = flush ? 0 : Math.max(0, lastAt.current + intervalMs - Date.now())
    const timer = window.setTimeout(() => {
      lastAt.current = Date.now()
      setSpoken(text)
    }, wait)
    return () => window.clearTimeout(timer)
  }, [text, spoken, intervalMs, flush])
  return spoken
}

/**
 * A visually hidden polite live region for a planning run: scouts finishing, the critic's issues,
 * the map step and the final result. Keep it mounted across the running → done transition.
 */
export function ProgressAnnouncer({ state }: { state: TimelineState }) {
  const finished = state.status === "done" || state.status === "error"
  const text = useThrottledText(describeProgress(state), ANNOUNCE_EVERY_MS, finished)
  return (
    <Text srOnly role="status" aria-live="polite" aria-atomic="true">
      {text}
    </Text>
  )
}
