import { Box, Center, Container, Heading, Stack, Text } from "@chakra-ui/react"
import { Link } from "@tanstack/react-router"
import { type ReactNode, useEffect } from "react"
import { LogoMark } from "@/components/Logo"

/** Bigya's centred auth layout: logo, heading and one line of copy above the form. */
export function AuthLayout({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string
  subtitle: string
  children: ReactNode
  footer?: ReactNode
}) {
  useEffect(() => {
    document.title = `${title} · Travya`
  }, [title])

  return (
    <Center as="main" minH="100dvh" bg="bg.subtle" px="4" py="10">
      <Container maxW="sm" px="0">
        <Stack
          gap="6"
          bg="bg.panel"
          borderWidth="1px"
          borderRadius="card"
          boxShadow="card"
          px={{ base: "5", sm: "8" }}
          py="8"
        >
          <Stack align="center" textAlign="center" gap="2">
            <Link to="/" aria-label="Travya home">
              <LogoMark size={44} />
            </Link>
            <Heading as="h1" fontFamily="heading" size="2xl" fontWeight="600">
              {title}
            </Heading>
            <Text color="fg.muted" fontSize="sm">
              {subtitle}
            </Text>
          </Stack>
          {children}
        </Stack>
        {footer && (
          <Box textAlign="center" mt="5" fontSize="sm" color="fg.muted">
            {footer}
          </Box>
        )}
      </Container>
    </Center>
  )
}
