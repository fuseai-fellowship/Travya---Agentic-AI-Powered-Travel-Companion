import { Alert, Box, Button, Collapsible, HStack, Spinner, Text } from "@chakra-ui/react"
import { LuChevronDown, LuX } from "react-icons/lu"
import { formatElapsed } from "@/lib/format"
import { AgentTimeline } from "./AgentTimeline"
import { dismissPlan, type PlanRun } from "./planStore"

/**
 * The live agent timeline while a plan runs here; a collapsible log afterwards; a polling notice
 * when the trip is planning in another tab.
 */
export function PlanningPanel({
  tripId,
  run,
  planningElsewhere,
  onRetry,
}: {
  tripId: string
  run: PlanRun | undefined
  planningElsewhere: boolean
  onRetry: () => void
}) {
  if (!run) {
    if (!planningElsewhere) return null
    return (
      <Alert.Root status="info" borderRadius="card">
        <Spinner size="sm" color="brand.solid" />
        <Alert.Content>
          <Alert.Title>The agents are planning this trip</Alert.Title>
          <Alert.Description>
            It was started elsewhere; this page updates when the plan is ready.
          </Alert.Description>
        </Alert.Content>
      </Alert.Root>
    )
  }

  const { state } = run
  if (state.status !== "done") {
    return (
      <Box p="4" borderWidth="1px" borderRadius="card" bg="bg.subtle">
        <AgentTimeline state={state} onRetry={run.active ? undefined : onRetry} />
      </Box>
    )
  }

  const total =
    state.startedAt !== null && state.finishedAt !== null
      ? state.finishedAt - state.startedAt
      : null
  return (
    <Collapsible.Root>
      <Box borderWidth="1px" borderRadius="card" bg="bg.subtle">
        <HStack justify="space-between" px="3" py="2" gap="2">
          <Collapsible.Trigger asChild>
            <Button variant="ghost" size="sm" flex="1" justifyContent="flex-start" minH="44px">
              <Text as="span" fontWeight="600">
                {state.headline}
              </Text>
              {total !== null && (
                <Text as="span" color="fg.muted" fontFamily="mono" fontSize="xs">
                  {formatElapsed(total)}
                </Text>
              )}
              <LuChevronDown aria-hidden="true" />
              <Text as="span" srOnly>
                Show the agent log
              </Text>
            </Button>
          </Collapsible.Trigger>
          <Button
            variant="ghost"
            size="sm"
            aria-label="Dismiss the agent log"
            onClick={() => dismissPlan(tripId)}
          >
            <LuX />
          </Button>
        </HStack>
        <Collapsible.Content>
          <Box px="4" pb="4">
            <AgentTimeline state={state} live={false} />
          </Box>
        </Collapsible.Content>
      </Box>
    </Collapsible.Root>
  )
}
