import {
  Box,
  Button,
  Link as ChakraLink,
  Container,
  Grid,
  Heading,
  HStack,
  Stack,
  Text,
} from "@chakra-ui/react"
import { Link } from "@tanstack/react-router"
import { DemoButton } from "@/features/auth/QuickSignIn"
import { Contours } from "./Contours"
import { LINKS } from "./links"
import { RunReplay } from "./RunReplay"
import { linkStyle } from "./Section"

export const HEADLINE = "A trip plan that checks its own work."

export function Hero({ signedIn }: { signedIn: boolean }) {
  return (
    <Box as="section" aria-labelledby="hero-title" position="relative" overflow="hidden">
      <Contours position="absolute" inset="0" fade display={{ base: "none", lg: "block" }} />
      <Container
        position="relative"
        maxW="7xl"
        px={{ base: "4", md: "8" }}
        pt={{ base: "8", md: "12" }}
        pb={{ base: "10", md: "14" }}
      >
        <Grid
          templateColumns={{ base: "minmax(0, 1fr)", lg: "minmax(0, 5fr) minmax(0, 7fr)" }}
          gap={{ base: "10", lg: "12" }}
          alignItems="start"
        >
          <Stack gap="6" pt={{ lg: "10" }} maxW="xl">
            <Heading
              as="h1"
              id="hero-title"
              fontSize={{ base: "4xl", md: "5xl", xl: "6xl" }}
              fontWeight="800"
              lineHeight="1.02"
              letterSpacing="-0.03em"
            >
              {HEADLINE}
            </Heading>
            <Text fontSize={{ base: "lg", md: "xl" }} color="fg.muted" maxW="lg" lineHeight="1.5">
              AI scouts pull weather, places and prices in parallel; a critic sends weak drafts
              back. You approve every booking.
            </Text>
            <Stack gap="3">
              <HStack gap="5" flexWrap="wrap" rowGap="3">
                {signedIn ? (
                  <Button asChild size="lg" colorPalette="brand">
                    <Link to="/trips">Open your trips</Link>
                  </Button>
                ) : (
                  <DemoButton size="lg" />
                )}
                <ChakraLink
                  href={LINKS.repo}
                  target="_blank"
                  rel="noopener noreferrer"
                  fontWeight="600"
                  {...linkStyle}
                >
                  Read the code
                </ChakraLink>
              </HStack>
              <Text fontSize="sm" color="fg.muted">
                Anonymous session. Bookings simulated; nothing charged.
              </Text>
            </Stack>
          </Stack>
          <RunReplay />
        </Grid>
      </Container>
    </Box>
  )
}
