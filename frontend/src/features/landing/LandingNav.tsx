import { Box, Button, Link as ChakraLink, Container, Flex, HStack } from "@chakra-ui/react"
import { Link } from "@tanstack/react-router"
import { LuGithub } from "react-icons/lu"
import { Logo } from "@/components/Logo"
import { ColorModeButton } from "@/components/ui/color-mode"
import { LINKS } from "./links"

export function LandingNav({ signedIn }: { signedIn: boolean }) {
  return (
    <Box as="header" borderBottomWidth="1px" bg="bg">
      <Container maxW="7xl" px={{ base: "4", md: "8" }}>
        <Flex as="nav" aria-label="Main" justify="space-between" align="center" h="14" gap="3">
          <Link to="/" aria-label="Travya home">
            <Logo />
          </Link>
          <HStack gap={{ base: "0", md: "1" }} fontSize="sm">
            <ChakraLink
              href="#how"
              display={{ base: "none", md: "inline-flex" }}
              px="3"
              py="2"
              color="fg.muted"
              _hover={{ color: "fg" }}
            >
              How it works
            </ChakraLink>
            <ChakraLink
              href={LINKS.evals}
              target="_blank"
              rel="noopener noreferrer"
              display={{ base: "none", md: "inline-flex" }}
              px="3"
              py="2"
              color="fg.muted"
              _hover={{ color: "fg" }}
            >
              Evals
            </ChakraLink>
            <ChakraLink
              href={LINKS.repo}
              target="_blank"
              rel="noopener noreferrer"
              px="3"
              py="2"
              color="fg.muted"
              _hover={{ color: "fg" }}
              gap="1.5"
            >
              <LuGithub aria-hidden="true" />
              GitHub
            </ChakraLink>
            <ColorModeButton size="sm" />
            {signedIn ? (
              <Button asChild size="sm" variant="outline">
                <Link to="/trips">Your trips</Link>
              </Button>
            ) : (
              <Button asChild size="sm" variant="outline">
                <Link to="/login">Sign in</Link>
              </Button>
            )}
          </HStack>
        </Flex>
      </Container>
    </Box>
  )
}
