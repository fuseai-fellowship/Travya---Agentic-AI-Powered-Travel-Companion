import { Box, Link as ChakraLink, Container, SimpleGrid, Stack, Text } from "@chakra-ui/react"
import { LINKS } from "./links"
import { linkStyle } from "./Section"

/** Live eval results from docs/evals.md (six golden trips, Gemini free tier). */
export const PROOF = [
  { value: "6/6", unit: "", label: "plans pass every hard check", detail: "dates, pace, budget" },
  {
    value: "96",
    unit: "%",
    label: "of named places land on the map",
    detail: "geocoded near the trip",
  },
  {
    value: "32",
    unit: "s",
    label: "median time to a full plan",
    detail: "research, draft, review",
  },
] as const

export function ProofRow() {
  return (
    <Box as="section" aria-labelledby="proof-title" borderTopWidth="1px" bg="bg.subtle">
      <Container maxW="7xl" px={{ base: "4", md: "8" }} py={{ base: "8", md: "10" }}>
        <Text as="h2" id="proof-title" srOnly>
          Measured results
        </Text>
        <SimpleGrid columns={{ base: 1, sm: 3 }} gap={{ base: "5", md: "8" }}>
          {PROOF.map((item) => (
            <Stack key={item.value} gap="0.5">
              <Text
                fontFamily="mono"
                fontSize={{ base: "3xl", md: "4xl" }}
                fontWeight="600"
                lineHeight="1"
                letterSpacing="-0.02em"
                style={{ fontVariantNumeric: "tabular-nums" }}
              >
                {item.value}
                {item.unit && (
                  <Text
                    as="span"
                    fontFamily="body"
                    fontSize="0.6em"
                    ms={item.unit === "s" ? "1" : "0"}
                  >
                    {item.unit}
                  </Text>
                )}
              </Text>
              <Text fontWeight="600">{item.label}</Text>
              <Text fontSize="sm" color="fg.muted">
                {item.detail}
              </Text>
            </Stack>
          ))}
        </SimpleGrid>
        <Text fontSize="sm" color="fg.muted" mt="6" maxW="3xl">
          Six golden trips on the live free tier, n = 6, scored in code.{" "}
          <ChakraLink href={LINKS.evals} target="_blank" rel="noopener noreferrer" {...linkStyle}>
            Method and reports
          </ChakraLink>{" "}
          ·{" "}
          <ChakraLink
            href={LINKS.evalRunner}
            target="_blank"
            rel="noopener noreferrer"
            {...linkStyle}
          >
            eval script
          </ChakraLink>
          . MIT licensed. Data from OpenStreetMap, Wikivoyage, Wikipedia and Open-Meteo.
        </Text>
      </Container>
    </Box>
  )
}
