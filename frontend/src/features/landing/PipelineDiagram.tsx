import { Box, Heading, HStack, Icon, Stack, Text } from "@chakra-ui/react"
import type { IconType } from "react-icons"
import {
  LuArrowRight,
  LuBookOpen,
  LuCloudSun,
  LuMapPin,
  LuPenLine,
  LuRepeat,
  LuShieldCheck,
  LuTicket,
  LuUserCheck,
} from "react-icons/lu"

const SCOUTS: Array<{ label: string; icon: IconType; source: string }> = [
  { label: "Weather", icon: LuCloudSun, source: "Open-Meteo" },
  { label: "Places", icon: LuMapPin, source: "OpenStreetMap" },
  { label: "Guide", icon: LuBookOpen, source: "Wikivoyage (RAG)" },
  { label: "Booking", icon: LuTicket, source: "sample quotes" },
]

const STAGES: Array<{ label: string; icon: IconType; text: string }> = [
  {
    label: "Planner",
    icon: LuPenLine,
    text: "Drafts a structured day-by-day plan from the research.",
  },
  {
    label: "Critic ⇄ Reviser",
    icon: LuRepeat,
    text: "Up to two review rounds; a quality gate adds hard checks.",
  },
  {
    label: "Quality gate",
    icon: LuShieldCheck,
    text: "Dates, pace and budget checked in code, not by the model.",
  },
  {
    label: "You confirm",
    icon: LuUserCheck,
    text: "Nothing is booked by an agent. You confirm quotes yourself.",
  },
]

/** The agent pipeline as an ordered list, laid out horizontally on wide screens. */
export function PipelineDiagram() {
  return (
    <Stack
      as="ol"
      direction={{ base: "column", lg: "row" }}
      gap="3"
      listStyleType="none"
      align="stretch"
    >
      <Stack as="li" flex="1.4" gap="2" p="4" borderWidth="1px" borderRadius="card" bg="bg.panel">
        <Text
          fontSize="xs"
          fontWeight="600"
          color="fg.muted"
          textTransform="uppercase"
          letterSpacing="wider"
        >
          1 · Four scouts in parallel
        </Text>
        <Box display="grid" gridTemplateColumns="1fr 1fr" gap="2">
          {SCOUTS.map((scout) => (
            <HStack key={scout.label} gap="2" p="2" borderRadius="md" bg="bg.subtle">
              <Icon as={scout.icon} color="sea.fg" aria-hidden="true" />
              <Stack gap="0">
                <Text fontSize="sm" fontWeight="600">
                  {scout.label}
                </Text>
                <Text fontSize="xs" color="fg.muted">
                  {scout.source}
                </Text>
              </Stack>
            </HStack>
          ))}
        </Box>
      </Stack>
      {STAGES.map((stage, index) => (
        <HStack as="li" key={stage.label} flex="1" gap="3" align="stretch">
          <Icon
            as={LuArrowRight}
            display={{ base: "none", lg: "block" }}
            alignSelf="center"
            color="fg.subtle"
            aria-hidden="true"
          />
          <Stack gap="1.5" p="4" borderWidth="1px" borderRadius="card" bg="bg.panel" flex="1">
            <Text
              fontSize="xs"
              fontWeight="600"
              color="fg.muted"
              textTransform="uppercase"
              letterSpacing="wider"
            >
              {index + 2}
            </Text>
            <HStack gap="2">
              <Icon as={stage.icon} color="brand.fg" aria-hidden="true" />
              <Heading as="h3" size="sm">
                {stage.label}
              </Heading>
            </HStack>
            <Text fontSize="sm" color="fg.muted">
              {stage.text}
            </Text>
          </Stack>
        </HStack>
      ))}
    </Stack>
  )
}
