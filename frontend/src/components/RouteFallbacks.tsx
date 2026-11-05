import { Box, Button, Center, Heading, Spinner, Text, VStack } from "@chakra-ui/react"
import { type ErrorComponentProps, Link } from "@tanstack/react-router"
import { errorMessage } from "@/lib/errors"

export function RoutePending() {
  return (
    <Center minH="40vh" role="status" aria-label="Loading">
      <Spinner color="brand.solid" size="lg" />
    </Center>
  )
}

export function RouteError({ error, reset }: ErrorComponentProps) {
  return (
    <Center minH="50vh" px="6">
      <VStack gap="3" maxW="md" textAlign="center">
        <Heading as="h1" fontFamily="heading" size="2xl">
          Something went off-route
        </Heading>
        <Text color="fg.muted">{errorMessage(error)}</Text>
        <Button colorPalette="brand" onClick={reset}>
          Try again
        </Button>
      </VStack>
    </Center>
  )
}

export function NotFound() {
  return (
    <Center minH="60vh" px="6">
      <VStack gap="3" maxW="md" textAlign="center">
        <Text fontFamily="mono" color="brand.fg" fontSize="sm">
          404
        </Text>
        <Heading as="h1" fontFamily="heading" size="2xl">
          This page isn't on the map
        </Heading>
        <Text color="fg.muted">The link may be old, or the trip was deleted.</Text>
        <Box>
          <Button asChild colorPalette="brand">
            <Link to="/trips">Back to your trips</Link>
          </Button>
        </Box>
      </VStack>
    </Center>
  )
}
