import { Box, Container, HStack, Link, Stack, Text } from "@chakra-ui/react"
import { LuGithub } from "react-icons/lu"
import { Logo } from "@/components/Logo"
import { REPO_URL } from "@/lib/env"

const CREDITS = [
  { label: "© OpenStreetMap contributors", href: "https://www.openstreetmap.org/copyright" },
  { label: "Wikivoyage (CC BY-SA)", href: "https://www.wikivoyage.org/" },
  { label: "Open-Meteo", href: "https://open-meteo.com/" },
  { label: "Unsplash", href: "https://unsplash.com/" },
  { label: "OpenFreeMap", href: "https://openfreemap.org/" },
]

export function LandingFooter() {
  return (
    <Box as="footer" borderTopWidth="1px" bg="bg.subtle" mt="20">
      <Container maxW="6xl" py="10" px={{ base: "4", md: "8" }}>
        <Stack gap="6" direction={{ base: "column", md: "row" }} justify="space-between">
          <Stack gap="3" maxW="sm">
            <Logo />
            <Text fontSize="sm" color="fg.muted">
              Built during the FuseAI Fellowship by Tilak Parajuli and Bigya.
            </Text>
            <Link
              href={REPO_URL}
              target="_blank"
              rel="noopener noreferrer"
              fontSize="sm"
              color="fg"
            >
              <LuGithub aria-hidden="true" /> Source on GitHub
            </Link>
          </Stack>
          <Stack gap="2">
            <Text fontSize="sm" fontWeight="600">
              Data and maps
            </Text>
            <HStack as="ul" gap="4" flexWrap="wrap" listStyleType="none" fontSize="sm" rowGap="1">
              {CREDITS.map((credit) => (
                <li key={credit.href}>
                  <Link
                    href={credit.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    color="fg.muted"
                  >
                    {credit.label}
                  </Link>
                </li>
              ))}
            </HStack>
            <Text fontSize="xs" color="fg.muted" maxW="md">
              Bookings in the demo are simulated. The assistant and planner run on Gemini's free
              tier.
            </Text>
          </Stack>
        </Stack>
      </Container>
    </Box>
  )
}
