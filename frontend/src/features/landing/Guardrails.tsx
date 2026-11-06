import { Link as ChakraLink, SimpleGrid, Stack, Text } from "@chakra-ui/react"
import { LINKS } from "./links"
import { Section } from "./Section"

const GUARDRAILS = [
  {
    title: "Hard checks in code",
    text: "Every trip date covered, no extra days, activities per day within the pace, total within budget. The model doesn't grade itself.",
    path: "backend/app/agents/planning/checks.py",
    href: LINKS.checks,
  },
  {
    title: "A critic loop with a cap",
    text: "The critic's issues and the failed checks go back to a reviser, at most twice. The issues stay visible in the timeline.",
    path: "backend/app/agents/planning/pipeline.py",
    href: LINKS.pipeline,
  },
  {
    title: "Places that exist",
    text: "Each named stop is matched to researched places or geocoded, and kept only if it is near the trip. Otherwise it stays off the map.",
    path: "backend/app/services/planning.py",
    href: LINKS.planning,
  },
  {
    title: "You approve bookings",
    text: "Agents only collect sample quotes. Nothing is booked until you confirm it, and every booking in the demo is simulated.",
    path: "backend/app/integrations/offers/sample.py",
    href: LINKS.offers,
  },
  {
    title: "Your data stays yours",
    text: "Every query is scoped to the signed-in owner, and an isolation test tries to read another user's trips through each endpoint.",
    path: "backend/tests/api/test_isolation.py",
    href: LINKS.isolation,
  },
  {
    title: "Rate limits and a budget",
    text: "Per-user rate limits and a daily model budget keep the free tier usable; when it runs out, the demo says so.",
    path: "backend/app/core/ratelimit.py",
    href: LINKS.ratelimit,
  },
] as const

export function Guardrails() {
  return (
    <Section
      id="guardrails"
      title="Guardrails, for engineers"
      lead="Where the plan is checked, and where to read the code."
    >
      <SimpleGrid as="ul" listStyleType="none" columns={{ base: 1, md: 2, xl: 3 }} gap="0">
        {GUARDRAILS.map((item) => (
          <Stack as="li" key={item.title} gap="1.5" py="5" pe={{ md: "8" }} borderTopWidth="1px">
            <Text fontWeight="700">{item.title}</Text>
            <Text color="fg.muted" fontSize="sm" lineHeight="1.55">
              {item.text}
            </Text>
            <ChakraLink
              href={item.href}
              target="_blank"
              rel="noopener noreferrer"
              fontFamily="mono"
              fontSize="xs"
              color="brand.fg"
              alignSelf="flex-start"
              wordBreak="break-all"
            >
              {item.path}
            </ChakraLink>
          </Stack>
        ))}
      </SimpleGrid>
    </Section>
  )
}
