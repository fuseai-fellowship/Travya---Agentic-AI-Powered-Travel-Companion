import { HStack, Icon, Spinner, Stack, Text } from "@chakra-ui/react"
import type { IconType } from "react-icons"
import { LuCircleAlert, LuCircleCheck, LuCircleDashed } from "react-icons/lu"
import { formatElapsed } from "@/lib/format"
import type { Step } from "./timeline"

export function StepStatusIcon({ status }: { status: Step["status"] }) {
  if (status === "running") return <Spinner size="xs" color="brand.solid" aria-hidden="true" />
  if (status === "done") return <Icon as={LuCircleCheck} color="sea.solid" aria-hidden="true" />
  if (status === "error") return <Icon as={LuCircleAlert} color="red.fg" aria-hidden="true" />
  return <Icon as={LuCircleDashed} color="fg.subtle" aria-hidden="true" />
}

const STATUS_TEXT: Record<Step["status"], string> = {
  pending: "waiting",
  running: "working",
  done: "done",
  error: "failed",
}

export function elapsedOf(step: Step, now: number): string | null {
  if (step.startedAt === null) return null
  return formatElapsed((step.finishedAt ?? now) - step.startedAt)
}

export function ScoutLane({
  label,
  icon,
  step,
  now,
  compact = false,
  highlighted = false,
}: {
  label: string
  icon: IconType
  step: Step
  now: number
  compact?: boolean
  highlighted?: boolean
}) {
  const elapsed = elapsedOf(step, now)
  return (
    <Stack
      as="li"
      gap={compact ? "1" : "1.5"}
      p={compact ? "2" : "3"}
      borderWidth="1px"
      borderRadius="card"
      bg={step.status === "running" ? "brand.subtle" : "bg.panel"}
      borderColor={
        highlighted ? "brand.focusRing" : step.status === "running" ? "brand.emphasized" : "border"
      }
      outline={highlighted ? "1px solid" : "none"}
      outlineColor="brand.focusRing"
      minH={compact ? "76px" : "92px"}
      data-status={step.status}
    >
      <HStack justify="space-between" gap="2">
        <HStack gap="2" minW="0">
          <Icon as={icon} color="fg.muted" aria-hidden="true" flexShrink={0} />
          <Text fontWeight="600" fontSize="sm">
            {label}
          </Text>
        </HStack>
        <StepStatusIcon status={step.status} />
        <Text srOnly>{STATUS_TEXT[step.status]}</Text>
      </HStack>
      <Text fontSize="xs" color="fg.muted" lineClamp={2}>
        {elapsed && (
          <Text
            as="span"
            fontFamily="mono"
            color="fg"
            whiteSpace="nowrap"
            style={{ fontVariantNumeric: "tabular-nums" }}
          >
            {elapsed}
            {" · "}
          </Text>
        )}
        {step.message || (step.status === "pending" ? "Waiting to start" : "Researching…")}
      </Text>
    </Stack>
  )
}
