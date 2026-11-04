import {
  Alert,
  Box,
  Button,
  Heading,
  HStack,
  List,
  SimpleGrid,
  Stack,
  Text,
} from "@chakra-ui/react"
import type { IconType } from "react-icons"
import { LuBookOpen, LuCloudSun, LuMapPin, LuTicket } from "react-icons/lu"
import { formatElapsed } from "@/lib/format"
import { useNow } from "@/lib/hooks"
import { elapsedOf, ScoutLane, StepStatusIcon } from "./ScoutLane"
import {
  AGENT_LABELS,
  SCOUTS,
  type ScoutId,
  STAGES,
  type StageId,
  type TimelineState,
} from "./timeline"
import { WeatherStrip } from "./WeatherStrip"

const SCOUT_ICONS: Record<ScoutId, IconType> = {
  weather_scout: LuCloudSun,
  places_scout: LuMapPin,
  guide_scout: LuBookOpen,
  offers_scout: LuTicket,
}

export function AgentTimeline({
  state,
  live = true,
  clock,
  onRetry,
}: {
  state: TimelineState
  /** Announce progress to screen readers (off for the landing page replay and old logs). */
  live?: boolean
  /** Overrides the wall clock, e.g. with a replay's own time. */
  clock?: number
  onRetry?: () => void
}) {
  const running = state.status === "running"
  const wallClock = useNow(running && clock === undefined)
  const now = clock ?? wallClock
  const total = state.startedAt === null ? null : (state.finishedAt ?? now) - state.startedAt
  const stages = STAGES.filter(
    (id) => state.status !== "done" || state.steps[id].status !== "pending",
  )

  return (
    <Stack gap="5" aria-busy={running}>
      <HStack justify="space-between" align="baseline" gap="3">
        <Heading as="h2" fontFamily="heading" size="lg" aria-live={live ? "polite" : "off"}>
          {state.status === "done"
            ? state.headline
            : state.status === "error"
              ? "Planning stopped"
              : "The agents are planning"}
        </Heading>
        {total !== null && (
          <Text
            fontFamily="mono"
            fontSize="sm"
            color="fg.muted"
            style={{ fontVariantNumeric: "tabular-nums" }}
          >
            {formatElapsed(total)}
          </Text>
        )}
      </HStack>

      <Box>
        <Text
          fontSize="xs"
          fontWeight="600"
          color="fg.muted"
          textTransform="uppercase"
          letterSpacing="wider"
          mb="2"
        >
          Research, in parallel
        </Text>
        <SimpleGrid as="ul" columns={{ base: 2, xl: 4 }} gap="2" listStyleType="none">
          {SCOUTS.map((id) => (
            <ScoutLane
              key={id}
              label={AGENT_LABELS[id]}
              icon={SCOUT_ICONS[id]}
              step={state.steps[id]}
              now={now}
            />
          ))}
        </SimpleGrid>
      </Box>

      <WeatherStrip days={state.weather} />

      <Stack as="ol" gap="0" listStyleType="none" borderLeftWidth="2px" ms="2">
        {stages.map((id) => (
          <StageRow key={id} id={id} state={state} now={now} />
        ))}
      </Stack>

      {state.status === "error" && (
        <Alert.Root status="error" borderRadius="card">
          <Alert.Indicator />
          <Alert.Content gap="2">
            <Alert.Title>{state.error}</Alert.Title>
            {onRetry && (
              <Button size="sm" variant="outline" alignSelf="flex-start" onClick={onRetry}>
                Try again
              </Button>
            )}
          </Alert.Content>
        </Alert.Root>
      )}
    </Stack>
  )
}

function StageRow({ id, state, now }: { id: StageId; state: TimelineState; now: number }) {
  const step = state.steps[id]
  const elapsed = elapsedOf(step, now)
  const muted = step.status === "pending"
  return (
    <Box
      as="li"
      position="relative"
      ps="5"
      py="2.5"
      opacity={muted ? 0.6 : 1}
      transition="opacity 200ms ease-out"
    >
      <Box position="absolute" left="-9px" top="3" bg="bg" lineHeight="0">
        <StepStatusIcon status={step.status} />
      </Box>
      <HStack justify="space-between" gap="2">
        <Text fontWeight="600" fontSize="sm">
          {AGENT_LABELS[id]}
          {step.runs > 1 && (
            <Text as="span" color="fg.muted" fontWeight="normal">
              {" "}
              · round {step.runs}
            </Text>
          )}
        </Text>
        {elapsed && (
          <Text
            fontFamily="mono"
            fontSize="xs"
            color="fg.muted"
            style={{ fontVariantNumeric: "tabular-nums" }}
          >
            {elapsed}
          </Text>
        )}
      </HStack>
      {step.message && (
        <Text fontSize="sm" color="fg.muted">
          {step.message}
        </Text>
      )}
      {id === "critic" && state.issues.length > 0 && (
        <List.Root gap="1" mt="2" ps="4" fontSize="sm">
          {state.issues.map((issue) => (
            <List.Item
              key={`${issue.round}-${issue.text}`}
              textDecoration={issue.resolved ? "line-through" : "none"}
              color={issue.resolved ? "fg.muted" : "fg"}
            >
              {issue.text}
              {issue.resolved && (
                <Text as="span" srOnly>
                  {" "}
                  (fixed by the reviser)
                </Text>
              )}
            </List.Item>
          ))}
        </List.Root>
      )}
    </Box>
  )
}
