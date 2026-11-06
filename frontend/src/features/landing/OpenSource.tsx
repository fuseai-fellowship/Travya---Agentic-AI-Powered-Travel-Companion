import { Box, Link as ChakraLink, Code, Grid, Heading, HStack, Stack, Text } from "@chakra-ui/react"
import { LINKS } from "./links"
import { linkStyle, Section } from "./Section"

const SELF_HOST = `git clone ${LINKS.repo}.git travya
cd travya && cp .env.example .env
docker compose up --build`

/** Open source and self-hosting, then who built it. */
export function OpenSource() {
  return (
    <Section id="code" title="Read how it plans. Run it yourself.">
      <Grid
        templateColumns={{ base: "minmax(0, 1fr)", lg: "minmax(0, 3fr) minmax(0, 2fr)" }}
        gap={{ base: "10", lg: "16" }}
      >
        <Stack gap="4">
          <Text color="fg.muted" fontSize={{ base: "md", md: "lg" }} maxW="2xl">
            MIT licensed. The default <Code fontSize="0.9em">.env</Code> runs everything offline
            with fakes and a scripted planner, so you need no keys to try the full flow; add a
            Gemini key for the real agents.
          </Text>
          <Box
            as="pre"
            fontFamily="mono"
            fontSize="sm"
            lineHeight="1.7"
            p="4"
            bg="bg.subtle"
            borderWidth="1px"
            borderRadius="card"
            whiteSpace="pre-wrap"
            wordBreak="break-all"
            aria-label="Self-host with Docker Compose"
          >
            <code>{SELF_HOST}</code>
          </Box>
          <HStack gap="5" flexWrap="wrap" fontSize="sm" fontWeight="600">
            <ChakraLink href={LINKS.repo} target="_blank" rel="noopener noreferrer" {...linkStyle}>
              Source on GitHub
            </ChakraLink>
            <ChakraLink href={LINKS.docs} target="_blank" rel="noopener noreferrer" {...linkStyle}>
              Architecture docs
            </ChakraLink>
            <ChakraLink
              href={LINKS.contributing}
              target="_blank"
              rel="noopener noreferrer"
              {...linkStyle}
            >
              How to contribute
            </ChakraLink>
          </HStack>
        </Stack>
        <Stack gap="3" as="aside" aria-labelledby="builder-title">
          <Heading as="h3" id="builder-title" fontSize="lg" fontWeight="800">
            Who built it
          </Heading>
          <Text color="fg.muted" lineHeight="1.6">
            <ChakraLink
              href={LINKS.author}
              target="_blank"
              rel="noopener noreferrer"
              fontWeight="600"
              {...linkStyle}
            >
              Tilak Parajuli
            </ChakraLink>{" "}
            designed and built Travya during the{" "}
            <ChakraLink
              href={LINKS.fuseai}
              target="_blank"
              rel="noopener noreferrer"
              {...linkStyle}
            >
              FuseAI Fellowship
            </ChakraLink>
            : the agents, backend, infrastructure and this interface. Bigya Vijay Dhungana built the
            early landing and chat UI and co-wrote the literature review.
          </Text>
          <Text color="fg.muted" fontSize="sm">
            Questions or bugs:{" "}
            <ChakraLink
              href={LINKS.issues}
              target="_blank"
              rel="noopener noreferrer"
              {...linkStyle}
            >
              open an issue
            </ChakraLink>
            .
          </Text>
        </Stack>
      </Grid>
    </Section>
  )
}
