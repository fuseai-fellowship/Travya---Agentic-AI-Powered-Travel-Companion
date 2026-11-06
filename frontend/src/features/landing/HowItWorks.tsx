import { Box, HStack, Stack, Text } from "@chakra-ui/react"
import { useMemo } from "react"
import {
  describeProgress,
  replay,
  type Step,
  type TimelineState,
} from "@/features/planner/timeline"
import { usePrefersReducedMotion } from "@/lib/hooks"
import { setReplayHighlight, useReplayClock } from "./replayClock"
import { HERO_RUN } from "./runs"
import { Section } from "./Section"

type AgentId = keyof TimelineState["steps"]
type StationId = AgentId | "you"

interface Station {
  id: StationId
  name: string
  note: string
}

/** Scouts branch in from the left like feeder lines; the colours are the map's day colours. */
const SCOUTS: Array<Station & { y: number; color: string }> = [
  { id: "weather_scout", name: "Weather", note: "Open-Meteo", y: 46, color: "#E69F00" },
  { id: "places_scout", name: "Places", note: "Wikipedia, OSM", y: 106, color: "#D55E00" },
  { id: "guide_scout", name: "Guide", note: "Wikivoyage passages", y: 166, color: "#009E73" },
  { id: "offers_scout", name: "Booking", note: "sample quotes", y: 226, color: "#CC79A7" },
]

const MAIN: Array<Station & { x: number }> = [
  { id: "planner", name: "Planner", note: "drafts every day", x: 430 },
  { id: "critic", name: "Critic", note: "lists issues", x: 590 },
  { id: "quality_gate", name: "Quality gate", note: "checks in code", x: 750 },
  { id: "finalize", name: "Map", note: "geocodes each stop", x: 925 },
  { id: "you", name: "You", note: "confirm bookings", x: 1095 },
]

const REVISER: Station = { id: "reviser", name: "Reviser", note: "fixes, twice at most" }
const MAIN_Y = 136
const SCOUT_X = 176
const MERGE_X = 340
const ROUTE = "#0072B2"
const LOOP = "#56B4E9"

const statusOf = (state: TimelineState, id: StationId): Step["status"] =>
  id === "you" ? (state.status === "done" ? "running" : "pending") : state.steps[id].status

const STATUS_TEXT: Record<Step["status"], string> = {
  pending: "waiting",
  running: "working",
  done: "done",
  error: "failed",
}

function Line({
  d,
  color,
  drawn,
  reduced,
}: {
  d: string
  color: string
  drawn: boolean
  reduced: boolean
}) {
  return (
    <g fill="none" strokeLinecap="round" strokeLinejoin="round">
      <path d={d} stroke="var(--chakra-colors-border-emphasized)" strokeWidth="6" />
      <path
        d={d}
        stroke={color}
        strokeWidth="6"
        pathLength={1}
        strokeDasharray="1"
        style={{
          strokeDashoffset: drawn ? 0 : 1,
          transition: reduced
            ? "none"
            : "stroke-dashoffset var(--chakra-durations-map) var(--chakra-easings-map)",
        }}
      />
    </g>
  )
}

function StationDot({
  x,
  y,
  status,
  id,
}: {
  x: number
  y: number
  status: Step["status"]
  id: StationId
}) {
  const running = status === "running"
  return (
    // biome-ignore lint/a11y/noStaticElementInteractions: pointer-only highlight in an aria-hidden diagram; keyboard and screen-reader users get the same stations as a list
    <g
      onMouseEnter={() => id !== "you" && setReplayHighlight(id)}
      onMouseLeave={() => setReplayHighlight(null)}
      style={{ cursor: id === "you" ? "default" : "help" }}
      data-station={id}
      data-status={status}
    >
      {running && <circle cx={x} cy={y} r="17" fill="var(--chakra-colors-brand-muted)" />}
      <circle
        cx={x}
        cy={y}
        r="10"
        fill={status === "done" ? "var(--chakra-colors-fg)" : "var(--chakra-colors-bg-panel)"}
        stroke="var(--chakra-colors-fg)"
        strokeWidth="3"
      />
    </g>
  )
}

function Label({
  x,
  y,
  station,
  anchor = "middle",
}: {
  x: number
  y: number
  station: Station
  anchor?: "start" | "middle" | "end"
}) {
  return (
    <text x={x} y={y} textAnchor={anchor}>
      <tspan fontWeight="700" fontSize="16" fill="var(--chakra-colors-fg)">
        {station.name}
      </tspan>
      <tspan x={x} dy="19" fontSize="14" fill="var(--chakra-colors-fg-muted)">
        {station.note}
      </tspan>
    </text>
  )
}

/** The planning graph as a transit map; lines draw in as the hero replay reaches each stage. */
function TransitMap({ state, reduced }: { state: TimelineState; reduced: boolean }) {
  const s = (id: StationId) => statusOf(state, id)
  const done = (id: StationId) => s(id) === "done"
  const scoutsDone = SCOUTS.every((scout) => done(scout.id))
  const x = (id: StationId) => MAIN.find((station) => station.id === id)?.x ?? 0
  const loop = `M${x("quality_gate")} ${MAIN_Y} C ${x("quality_gate")} 250, ${x("critic")} 250, ${x("critic")} ${MAIN_Y}`
  const reviserX = (x("critic") + x("quality_gate")) / 2

  return (
    <svg viewBox="0 0 1176 300" width="100%" aria-hidden="true" style={{ overflow: "visible" }}>
      {SCOUTS.map((scout) => (
        <Line
          key={scout.id}
          d={`M${SCOUT_X} ${scout.y} H260 C 300 ${scout.y}, 300 ${MAIN_Y}, ${MERGE_X} ${MAIN_Y}`}
          color={scout.color}
          drawn={done(scout.id)}
          reduced={reduced}
        />
      ))}
      <Line
        d={`M${MERGE_X} ${MAIN_Y} H${x("planner")}`}
        color={ROUTE}
        drawn={scoutsDone}
        reduced={reduced}
      />
      <Line
        d={`M${x("planner")} ${MAIN_Y} H${x("critic")}`}
        color={ROUTE}
        drawn={done("planner")}
        reduced={reduced}
      />
      <Line
        d={`M${x("critic")} ${MAIN_Y} H${x("quality_gate")}`}
        color={ROUTE}
        drawn={state.steps.critic.runs > 0}
        reduced={reduced}
      />
      <Line d={loop} color={LOOP} drawn={state.steps.reviser.runs > 0} reduced={reduced} />
      <Line
        d={`M${x("quality_gate")} ${MAIN_Y} H${x("finalize")}`}
        color={ROUTE}
        drawn={s("finalize") !== "pending"}
        reduced={reduced}
      />
      <Line
        d={`M${x("finalize")} ${MAIN_Y} H${x("you")}`}
        color={ROUTE}
        drawn={state.status === "done"}
        reduced={reduced}
      />

      {SCOUTS.map((scout) => (
        <g key={scout.id}>
          <StationDot x={SCOUT_X} y={scout.y} status={s(scout.id)} id={scout.id} />
          <Label x={SCOUT_X - 22} y={scout.y - 3} station={scout} anchor="end" />
        </g>
      ))}
      {MAIN.map((station) => (
        <g key={station.id}>
          <StationDot x={station.x} y={MAIN_Y} status={s(station.id)} id={station.id} />
          <Label x={station.x} y={MAIN_Y - 44} station={station} />
        </g>
      ))}
      <StationDot x={reviserX} y={232} status={s("reviser")} id="reviser" />
      <Label x={reviserX} y={268} station={REVISER} />
    </svg>
  )
}

const ALL: Station[] = [...SCOUTS, MAIN[0], MAIN[1], MAIN[2], REVISER, MAIN[3], MAIN[4]].filter(
  (station): station is Station => Boolean(station),
)

/** The same stations as a list: the layout on phones, and what screen readers get everywhere. */
function StationList({ state }: { state: TimelineState }) {
  return (
    <Stack
      as="ol"
      listStyleType="none"
      gap="0"
      borderLeftWidth="3px"
      borderColor="brand.solid"
      ms="2"
    >
      {ALL.map((station) => {
        const status = statusOf(state, station.id)
        return (
          <HStack
            as="li"
            key={station.id}
            gap="3"
            py="1.5"
            ps="4"
            position="relative"
            align="start"
          >
            <Box
              position="absolute"
              left="-9.5px"
              top="2.5"
              boxSize="4"
              borderRadius="full"
              borderWidth="3px"
              borderColor="fg"
              bg={status === "done" ? "fg" : "bg.panel"}
              aria-hidden="true"
            />
            <Text>
              <Text as="span" fontWeight="700">
                {station.name}
              </Text>
              <Text as="span" fontSize="sm" color="fg.muted">
                {" · "}
                {station.note}
              </Text>
              <Text as="span" srOnly>
                {" "}
                ({STATUS_TEXT[status]} in the replay)
              </Text>
            </Text>
          </HStack>
        )
      })}
    </Stack>
  )
}

export function HowItWorks() {
  const { elapsed } = useReplayClock()
  const reduced = usePrefersReducedMotion()
  const state = useMemo(() => replay(HERO_RUN.events, elapsed), [elapsed])

  return (
    <Section
      id="how"
      title="How a plan gets made"
      lead="A Google ADK workflow on Gemini. Four scouts research at once, a planner drafts, a critic and checks in code review it, and every step streams to the page. Point at a station to find it in the run above."
    >
      <Box display={{ base: "none", lg: "block" }} px="2" py="4">
        <TransitMap state={state} reduced={reduced} />
      </Box>
      {/* Visible on phones; visually hidden (still read) next to the transit map. */}
      <Box
        position={{ lg: "absolute" }}
        w={{ lg: "1px" }}
        h={{ lg: "1px" }}
        overflow={{ lg: "hidden" }}
        clipPath={{ lg: "inset(50%)" }}
        whiteSpace={{ lg: "nowrap" }}
      >
        <StationList state={state} />
      </Box>
      <Text fontSize="sm" color="fg.muted" mt="6">
        <Text as="span" fontWeight="600" color="fg">
          In the recorded run above:
        </Text>{" "}
        {describeProgress(state) || "waiting to start."}
      </Text>
    </Section>
  )
}
