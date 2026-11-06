import { Box, Link as ChakraLink, Container, Grid, Stack, Text } from "@chakra-ui/react"
import type { ReactNode } from "react"
import { Logo } from "@/components/Logo"
import { Contours } from "./Contours"
import { LINKS } from "./links"

const CREDITS = [
  { label: "© OpenStreetMap contributors (ODbL)", href: "https://www.openstreetmap.org/copyright" },
  { label: "Wikivoyage, CC BY-SA", href: "https://www.wikivoyage.org/" },
  { label: "Wikipedia, CC BY-SA", href: "https://www.wikipedia.org/" },
  { label: "Open-Meteo, CC BY 4.0", href: "https://open-meteo.com/" },
  { label: "Unsplash", href: "https://unsplash.com/" },
  { label: "Map tiles: OpenFreeMap", href: "https://openfreemap.org/" },
]

function Column({ title, children }: { title: string; children: ReactNode }) {
  return (
    <Stack gap="2" fontSize="sm">
      <Text as="h2" fontWeight="700" fontSize="sm">
        {title}
      </Text>
      {children}
    </Stack>
  )
}

const muted = { color: "fg.muted", _hover: { color: "fg" } } as const

export function LandingFooter() {
  return (
    <Box as="footer" position="relative" borderTopWidth="1px" bg="bg.subtle" overflow="hidden">
      <Contours position="absolute" inset="0" opacity="0.6" />
      <Container position="relative" maxW="7xl" px={{ base: "4", md: "8" }} py="12">
        <Grid
          templateColumns={{ base: "minmax(0, 1fr)", md: "1.4fr 1fr 1fr 1fr" }}
          gap={{ base: "8", md: "10" }}
        >
          <Stack gap="3" maxW="sm">
            <Logo />
            <Text fontSize="sm" color="fg.muted">
              An open-source agentic travel planner, built by Tilak Parajuli during the FuseAI
              Fellowship. Early UI by Bigya.
            </Text>
          </Stack>
          <Column title="Data and maps">
            <Stack as="ul" listStyleType="none" gap="1">
              {CREDITS.map((credit) => (
                <li key={credit.href}>
                  <ChakraLink
                    href={credit.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    {...muted}
                  >
                    {credit.label}
                  </ChakraLink>
                </li>
              ))}
            </Stack>
          </Column>
          <Column title="Privacy">
            <Text color="fg.muted">
              The demo keeps your trips in an anonymous account. Planner and assistant run on
              Gemini's free tier, so don't enter personal information.
            </Text>
            <ChakraLink href={LINKS.security} target="_blank" rel="noopener noreferrer" {...muted}>
              Security and data handling
            </ChakraLink>
          </Column>
          <Column title="Project">
            <ChakraLink href={LINKS.issues} target="_blank" rel="noopener noreferrer" {...muted}>
              Contact: open an issue
            </ChakraLink>
            <ChakraLink href={LINKS.repo} target="_blank" rel="noopener noreferrer" {...muted}>
              Source (MIT)
            </ChakraLink>
            <ChakraLink href={LINKS.stars} target="_blank" rel="noopener noreferrer" {...muted}>
              Star on GitHub
            </ChakraLink>
            <Text color="fg.muted">Sponsor: not set up yet</Text>
          </Column>
        </Grid>
        <Text fontSize="xs" color="fg.muted" mt="10">
          Bookings in the demo are simulated: nothing is reserved or charged. Contour lines:
          Kathmandu Valley, 100 m interval, Copernicus GLO-90 via Open-Meteo.
        </Text>
      </Container>
    </Box>
  )
}
