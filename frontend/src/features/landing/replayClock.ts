import { useSyncExternalStore } from "react"

/**
 * Shared state of the hero replay: its position in the recorded run and the agent the visitor is
 * pointing at in the pipeline diagram. Lives outside React so only subscribers re-render per tick.
 */
interface ReplayClock {
  elapsed: number
  highlight: string | null
}

let clock: ReplayClock = { elapsed: 0, highlight: null }
const listeners = new Set<() => void>()

function emit(next: ReplayClock) {
  clock = next
  for (const listener of listeners) listener()
}

export function setReplayElapsed(elapsed: number) {
  if (elapsed !== clock.elapsed) emit({ ...clock, elapsed })
}

export function setReplayHighlight(highlight: string | null) {
  if (highlight !== clock.highlight) emit({ ...clock, highlight })
}

function subscribe(listener: () => void) {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export function useReplayClock(): ReplayClock {
  return useSyncExternalStore(
    subscribe,
    () => clock,
    () => clock,
  )
}
