import { Box, chakra } from "@chakra-ui/react"
import { useEffect } from "react"
import { useAuth } from "@/features/auth/AuthProvider"
import { HEALTH_URL } from "@/lib/api"
import { useDocumentTitle } from "@/lib/hooks"
import { warmServer } from "@/lib/wake"
import { Gallery } from "./Gallery"
import { Guardrails } from "./Guardrails"
import { Hero } from "./Hero"
import { HowItWorks } from "./HowItWorks"
import { LandingFooter } from "./LandingFooter"
import { LandingNav } from "./LandingNav"
import { OpenSource } from "./OpenSource"
import { ProofRow } from "./ProofRow"
import { RealRunVideo } from "./RealRunVideo"

/**
 * Pain → claim → proof, short: the hero shows a recorded production run, then the measured
 * results, a real run on video, how it works, guardrails, three real plans and the code.
 */
export function LandingPage() {
  useDocumentTitle("A trip plan that checks its own work")
  const { status } = useAuth()
  const signedIn = status === "signedIn"
  // Start waking the free API server while the visitor reads, so the demo is warm on click.
  useEffect(() => warmServer(HEALTH_URL), [])

  return (
    <Box bg="bg" minH="100dvh">
      <chakra.a
        href="#main"
        position="absolute"
        left="2"
        top="-20"
        zIndex="skipLink"
        bg="bg.panel"
        px="4"
        py="2"
        borderRadius="md"
        _focus={{ top: "2" }}
      >
        Skip to content
      </chakra.a>
      <LandingNav signedIn={signedIn} />
      <Box as="main" id="main">
        <Hero signedIn={signedIn} />
        <ProofRow />
        <RealRunVideo />
        <HowItWorks />
        <Guardrails />
        <Gallery />
        <OpenSource />
      </Box>
      <LandingFooter />
    </Box>
  )
}
