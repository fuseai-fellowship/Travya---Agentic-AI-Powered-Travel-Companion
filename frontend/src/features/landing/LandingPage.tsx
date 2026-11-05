import {
  Box,
  Button,
  Link as ChakraLink,
  Container,
  Flex,
  Grid,
  Heading,
  HStack,
  Stack,
  Text,
} from "@chakra-ui/react"
import { Link } from "@tanstack/react-router"
import { useEffect } from "react"
import { LuArrowRight, LuGithub } from "react-icons/lu"
import { Logo } from "@/components/Logo"
import { ColorModeButton } from "@/components/ui/color-mode"
import { useAuth } from "@/features/auth/AuthProvider"
import { DemoButton } from "@/features/auth/QuickSignIn"
import { HEALTH_URL } from "@/lib/api"
import { REPO_URL } from "@/lib/env"
import { useDocumentTitle } from "@/lib/hooks"
import { warmServer } from "@/lib/wake"
import { LandingFooter } from "./LandingFooter"
import { PipelineDiagram } from "./PipelineDiagram"
import { ReplayDemo } from "./ReplayDemo"

const STACK =
  "React 19 · TanStack Router & Query · Chakra UI · MapLibre · FastAPI · Google ADK · Gemini · PostgreSQL + pgvector · Cloud Run"

export function LandingPage() {
  useDocumentTitle("Watch AI agents plan your trip")
  const { status } = useAuth()
  const signedIn = status === "signedIn"
  // Start waking the free API server while the visitor reads, so the demo is warm on click.
  useEffect(() => warmServer(HEALTH_URL), [])

  return (
    <Box bg="bg" minH="100dvh">
      <Container as="header" maxW="6xl" px={{ base: "4", md: "8" }} py="4">
        <Flex justify="space-between" align="center" gap="3">
          <Logo />
          <HStack gap="1">
            <ChakraLink
              href={REPO_URL}
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Source on GitHub"
              p="2.5"
              color="fg.muted"
            >
              <LuGithub />
            </ChakraLink>
            <ColorModeButton size="sm" />
            {!signedIn && (
              <Button asChild variant="ghost" size="sm">
                <Link to="/login">Sign in</Link>
              </Button>
            )}
          </HStack>
        </Flex>
      </Container>

      <Box as="main" id="main">
        <Container maxW="6xl" px={{ base: "4", md: "8" }} pt={{ base: "6", md: "12" }}>
          <Grid
            templateColumns={{ base: "1fr", lg: "1fr 1.05fr" }}
            gap={{ base: "10", lg: "14" }}
            alignItems="start"
          >
            <Stack gap="6">
              <Heading
                as="h1"
                fontFamily="heading"
                fontWeight="600"
                fontSize={{ base: "4xl", md: "6xl" }}
                lineHeight="1.05"
                letterSpacing="-0.02em"
              >
                Watch a team of AI agents plan your trip.
              </Heading>
              <Text fontSize={{ base: "lg", md: "xl" }} color="fg.muted" maxW="xl">
                Scouts research weather, places, guides and prices in parallel. A planner drafts
                your days, a critic sends them back until they hold up, and you confirm what to
                book.
              </Text>
              <Stack direction={{ base: "column", sm: "row" }} gap="3">
                {signedIn ? (
                  <Button asChild size="lg" colorPalette="brand">
                    <Link to="/trips">
                      Open your trips <LuArrowRight />
                    </Link>
                  </Button>
                ) : (
                  <>
                    <DemoButton size="lg" />
                    <Button asChild size="lg" variant="outline">
                      <Link to="/login">Sign in</Link>
                    </Button>
                  </>
                )}
              </Stack>
              <Text fontSize="sm" color="fg.muted">
                The demo signs you in anonymously. Bookings are simulated; nothing is charged.
              </Text>
            </Stack>
            <ReplayDemo />
          </Grid>
        </Container>

        <Container
          as="section"
          aria-labelledby="how"
          maxW="6xl"
          px={{ base: "4", md: "8" }}
          mt={{ base: "16", md: "24" }}
        >
          <Stack gap="2" mb="6" maxW="2xl">
            <Heading as="h2" id="how" fontFamily="heading" fontWeight="600" size="2xl">
              How a plan is made
            </Heading>
            <Text color="fg.muted">
              A Google ADK pipeline: parallel research, a structured draft, then a critique loop
              with checks in code. Every agent's progress streams to the page as it happens.
            </Text>
          </Stack>
          <PipelineDiagram />
        </Container>

        <Container
          as="section"
          aria-labelledby="stack"
          maxW="6xl"
          px={{ base: "4", md: "8" }}
          mt={{ base: "16", md: "20" }}
        >
          <Heading as="h2" id="stack" fontFamily="heading" fontWeight="600" size="lg" mb="2">
            Under the hood
          </Heading>
          <Text color="fg.muted" fontFamily="mono" fontSize="sm">
            {STACK}
          </Text>
        </Container>
      </Box>
      <LandingFooter />
    </Box>
  )
}
