import { Box, Grid, HStack, IconButton, Text } from "@chakra-ui/react"
import { useEffect, useMemo, useRef, useState } from "react"
import { LuPause, LuPlay, LuRotateCcw } from "react-icons/lu"
import { AgentTimeline } from "@/features/planner/AgentTimeline"
import { replay } from "@/features/planner/timeline"
import { usePrefersReducedMotion } from "@/lib/hooks"
import heroDark from "./media/hero-kyoto-dark.webp"
import heroLight from "./media/hero-kyoto-light.webp"
import { RunMap } from "./RunMap"
import { setReplayElapsed, useReplayClock } from "./replayClock"
import { HERO_RUN, recordedOn } from "./runs"

/** Pause on the finished plan before the loop starts again. */
const HOLD_MS = 6000
const TICK_MS = 100
const RUN = HERO_RUN
const TOTAL = RUN.durationMs

const clockText = (ms: number) => {
  const seconds = Math.floor(ms / 1000)
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`
}

/**
 * The hero: the app's own AgentTimeline and a map, driven by a recorded production run at its
 * real speed (event offsets as the browser received them). Plays while on screen; pausable;
 * reduced motion shows the finished RUN.
 */
export function RunReplay() {
  const reducedMotion = usePrefersReducedMotion()
  const [elapsed, setElapsed] = useState(reducedMotion ? TOTAL : 0)
  const [playing, setPlaying] = useState(!reducedMotion)
  const [visible, setVisible] = useState(false)
  const root = useRef<HTMLDivElement>(null)
  const log = useRef<HTMLDivElement>(null)
  const elapsedRef = useRef(elapsed)
  elapsedRef.current = elapsed
  const { highlight } = useReplayClock()

  useEffect(() => {
    if (reducedMotion) {
      setPlaying(false)
      setElapsed(TOTAL)
    }
  }, [reducedMotion])

  // Only run the clock while the replay is on screen.
  useEffect(() => {
    const node = root.current
    if (!node || typeof IntersectionObserver === "undefined") {
      setVisible(true)
      return
    }
    const observer = new IntersectionObserver(([entry]) => setVisible(!!entry?.isIntersecting))
    observer.observe(node)
    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    if (!playing || !visible) return
    let started = performance.now() - elapsedRef.current
    const timer = window.setInterval(() => {
      let next = performance.now() - started
      if (next > TOTAL + HOLD_MS) {
        started = performance.now()
        next = 0
      }
      setElapsed(next)
    }, TICK_MS)
    return () => window.clearInterval(timer)
  }, [playing, visible])

  const position = Math.min(elapsed, TOTAL)
  useEffect(() => setReplayElapsed(position), [position])
  const state = useMemo(() => replay(RUN.events, position), [position])

  // Keep the newest step in view inside the log without scrolling the page.
  // biome-ignore lint/correctness/useExhaustiveDependencies: follow the replay as it advances
  useEffect(() => {
    const box = log.current
    if (!box || !playing) return
    const rows = box.querySelectorAll<HTMLElement>('[data-agent]:not([data-status="pending"])')
    const active = [...rows].at(-1)
    if (!active) return
    const bottom = active.offsetTop + active.offsetHeight + 16
    if (bottom > box.scrollTop + box.clientHeight) box.scrollTop = bottom - box.clientHeight
    if (position < 500) box.scrollTop = 0
  }, [state, playing])

  const done = state.status === "done"
  const toggle = () => {
    if (!playing && elapsed >= TOTAL) setElapsed(0)
    setPlaying((value) => !value)
  }

  return (
    <Box
      ref={root}
      as="figure"
      bg="bg.panel"
      borderWidth="1px"
      borderRadius="card"
      boxShadow="card"
      overflow="hidden"
      aria-label={`Recorded planning run: ${RUN.destination}, ${RUN.days} days`}
    >
      <HStack justify="space-between" gap="2" px="3" py="2" borderBottomWidth="1px">
        <Text as="figcaption" fontSize="sm" color="fg.muted" lineClamp={{ base: 2, md: 1 }}>
          <Text as="span" color="fg" fontWeight="600">
            Recorded run
          </Text>
          , {RUN.destination}, {RUN.days} days, {recordedOn(RUN.recordedAt)}, real speed
        </Text>
        <HStack gap="0" flexShrink={0}>
          <IconButton
            size="sm"
            variant="ghost"
            onClick={toggle}
            aria-label={playing ? "Pause the replay" : "Play the replay"}
          >
            {playing ? <LuPause /> : <LuPlay />}
          </IconButton>
          <IconButton
            size="sm"
            variant="ghost"
            aria-label="Restart the replay"
            onClick={() => {
              setElapsed(0)
              setPlaying(true)
            }}
          >
            <LuRotateCcw />
          </IconButton>
        </HStack>
      </HStack>

      <Grid
        templateColumns={{ base: "minmax(0, 1fr)", md: "minmax(0, 1fr) minmax(0, 1fr)" }}
        templateAreas={{ base: `"map" "log"`, md: `"log map"` }}
        h={{ base: "auto", md: "540px" }}
      >
        <Box
          ref={log}
          gridArea="log"
          h={{ base: "400px", md: "full" }}
          overflowY="auto"
          p="3"
          borderRightWidth={{ md: "1px" }}
          tabIndex={0}
          aria-label="Agent timeline"
        >
          <AgentTimeline
            state={state}
            clock={position}
            compact
            headingAs="h3"
            highlight={highlight}
          />
        </Box>
        <RunMap
          gridArea="map"
          h={{ base: "240px", md: "full" }}
          map={RUN.map}
          light={heroLight}
          dark={heroDark}
          priority
          showPlaces={state.places.length > 0}
          showStops={done}
          animate={!reducedMotion}
          label={
            done
              ? `Map of central ${RUN.destination} with the ${RUN.map.stops.length} planned stops and a route per day`
              : `Map of central ${RUN.destination}${state.places.length ? `, showing ${state.places.length} places the scouts found` : ""}`
          }
        />
      </Grid>

      <HStack gap="3" px="3" py="2" borderTopWidth="1px">
        <input
          type="range"
          min={0}
          max={TOTAL}
          step={100}
          value={position}
          onChange={(event) => {
            setElapsed(Number(event.target.value))
            setPlaying(false)
          }}
          aria-label="Position in the recorded run"
          aria-valuetext={`${Math.round(position / 1000)} of ${Math.round(TOTAL / 1000)} seconds`}
          style={{ flex: 1, accentColor: "var(--chakra-colors-brand-solid)" }}
        />
        <Text
          fontFamily="mono"
          fontSize="xs"
          color="fg.muted"
          style={{ fontVariantNumeric: "tabular-nums" }}
          aria-hidden="true"
        >
          {clockText(position)} / {clockText(TOTAL)}
        </Text>
      </HStack>
    </Box>
  )
}
