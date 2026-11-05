import { Box, Button, HStack, Stack, Text } from "@chakra-ui/react"
import { useEffect, useMemo, useRef, useState } from "react"
import { LuPause, LuPlay, LuRotateCcw } from "react-icons/lu"
import { AgentTimeline } from "@/features/planner/AgentTimeline"
import { replay } from "@/features/planner/timeline"
import { usePrefersReducedMotion } from "@/lib/hooks"
import { ReplayMap } from "./ReplayMap"
import { REPLAY_LENGTH, REPLAY_SCRIPT } from "./replayScript"

const HOLD_MS = 4000

/** The hero: the real timeline component driven by a scripted event stream, on a loop. */
export function ReplayDemo() {
  const reducedMotion = usePrefersReducedMotion()
  const [elapsed, setElapsed] = useState(reducedMotion ? REPLAY_LENGTH : 0)
  const [playing, setPlaying] = useState(!reducedMotion)
  const elapsedRef = useRef(elapsed)
  elapsedRef.current = elapsed

  useEffect(() => {
    if (reducedMotion) {
      setPlaying(false)
      setElapsed(REPLAY_LENGTH)
    }
  }, [reducedMotion])

  useEffect(() => {
    if (!playing) return
    let started = performance.now() - elapsedRef.current
    const timer = window.setInterval(() => {
      let next = performance.now() - started
      if (next > REPLAY_LENGTH + HOLD_MS) {
        started = performance.now()
        next = 0
      }
      setElapsed(next)
    }, 100)
    return () => window.clearInterval(timer)
  }, [playing])

  const state = useMemo(() => replay(REPLAY_SCRIPT, elapsed), [elapsed])

  return (
    <Stack
      gap="3"
      p={{ base: "4", md: "5" }}
      bg="bg.panel"
      borderWidth="1px"
      borderRadius="card"
      boxShadow="card"
    >
      <HStack justify="space-between">
        <Text
          fontSize="xs"
          color="fg.muted"
          textTransform="uppercase"
          letterSpacing="wider"
          fontWeight="600"
        >
          Replay · Kathmandu, 4 days
        </Text>
        <HStack gap="1">
          <Button
            size="xs"
            variant="ghost"
            onClick={() => setPlaying((value) => !value)}
            aria-label={playing ? "Pause the replay" : "Play the replay"}
          >
            {playing ? <LuPause /> : <LuPlay />}
          </Button>
          <Button
            size="xs"
            variant="ghost"
            aria-label="Restart the replay"
            onClick={() => {
              setElapsed(0)
              setPlaying(true)
            }}
          >
            <LuRotateCcw />
          </Button>
        </HStack>
      </HStack>
      <Box aria-hidden={playing ? true : undefined}>
        <AgentTimeline state={state} clock={elapsed} />
      </Box>
      <ReplayMap showPlaces={state.places.length > 0} showStops={state.status === "done"} />
    </Stack>
  )
}
