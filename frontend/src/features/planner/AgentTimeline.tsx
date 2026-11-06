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

/** The run's steps. Announcements live in `ProgressAnnouncer`, so this never speaks by itself. */
export function AgentTimeline({
  state,
  clock,
  onRetry,
  onStop,
  compact = false,
  highlight = null,
  headingAs = "h2",
}: {
  state: TimelineState
  /** Overrides the wall clock, e.g. with a replay's own time. */
  clock?: number
  onRetry?: () => void
  onStop?: () => void
  /** Tighter spacing and one line per message (the landing page replay). */
  compact?: boolean
  /** An agent to outline, e.g. while its node is hovered in the pipeline diagram. */
  highlight?: string | null
  headingAs?: "h2" | "h3"
}) {
  const running = state.status === "running"
  const wallClock = useNow(running && clock === undefined)
  const now = clock ?? wallClock
  const total = state.startedAt === null ? null : (state.finishedAt ?? now) - state.startedAt
  const stages = STAGES.filter(
    (id) => state.status !== "done" || state.steps[id].status !== "pending",
  )

  return (
    <Stack gap={compact ? "3" : "5"} aria-busy={running}>
      <HStack
        justify="space-between"
        align="baseline"
        gap="3"
        // In the replay's scrolling log the heading and clock stay in view.
        {...(compact
          ? { position: "sticky", top: "-3", zIndex: "1", bg: "bg.panel", py: "1.5", mt: "-1.5" }
          : {})}
      >
        <Heading as={headingAs} size={compact ? "md" : "lg"} lineHeight="1.2">
          {state.status === "done"
            ? state.headline
            : state.status === "error"
              ? "Planning stopped"
              : "The agents are planning"}
        </Heading>
        <HStack gap="2">
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
          {running && onStop && (
            <Button size="xs" variant="outline" onClick={onStop}>
              Stop
            </Button>
          )}
        </HStack>
      </HStack>

      <Box>
        <Text fontSize="sm" color="fg.muted" mb="2">
          Research, in parallel
        </Text>
        <SimpleGrid as="ul" columns={2} gap="2" listStyleType="none">
          {SCOUTS.map((id) => (
            <ScoutLane
              key={id}
              label={AGENT_LABELS[id]}
              icon={SCOUT_ICONS[id]}
              step={state.steps[id]}
              now={now}
              compact={compact}
              highlighted={highlight === id}
            />
          ))}
        </SimpleGrid>
      </Box>

      {!compact && <WeatherStrip days={state.weather} />}

      <Stack as="ol" gap="0" listStyleType="none" borderLeftWidth="2px" ms="2">
        {stages.map((id) => (
          <StageRow
            key={id}
            id={id}
            state={state}
            now={now}
            compact={compact}
            highlighted={highlight === id}
          />
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

function StageRow({
  id,
  state,
  now,
  compact,
  highlighted,
}: {
  id: StageId
  state: TimelineState
  now: number
  compact: boolean
  highlighted: boolean
}) {
  const step = state.steps[id]
  const elapsed = elapsedOf(step, now)
  const muted = step.status === "pending"
  return (
    <Box
      as="li"
      position="relative"
      ps="5"
      py={compact ? "1.5" : "2.5"}
      opacity={muted ? 0.6 : 1}
      borderRadius="sm"
      outline={highlighted ? "2px solid" : "none"}
      outlineColor="brand.focusRing"
      outlineOffset="-2px"
      data-agent={id}
      data-status={step.status}
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
        <Text fontSize="sm" color="fg.muted" lineClamp={compact ? 1 : undefined}>
          {step.message}
        </Text>
      )}
      {id === "critic" && state.issues.length > 0 && (
        <List.Root gap="1" mt={compact ? "1" : "2"} ps="4" fontSize={compact ? "xs" : "sm"}>
          {state.issues.map((issue) => (
            <List.Item
              key={`${issue.round}-${issue.text}`}
              textDecoration={issue.resolved ? "line-through" : "none"}
              color={issue.resolved ? "fg.muted" : "fg"}
              lineClamp={compact ? 1 : undefined}
              title={compact ? issue.text : undefined}
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
