import { Box, Heading, LinkBox, LinkOverlay, SimpleGrid, Text } from "@chakra-ui/react"
import { Link } from "@tanstack/react-router"
import { plural } from "@/lib/format"
import { SAMPLE_TRIPS } from "./samples"

/** One-click starting points that prefill the new-trip form. */
export function SampleTrips() {
  return (
    <SimpleGrid as="ul" columns={{ base: 1, sm: 3 }} gap="3" w="full" listStyleType="none">
      {SAMPLE_TRIPS.map((sample) => (
        <LinkBox
          as="li"
          key={sample.id}
          p="4"
          bg="bg.panel"
          borderWidth="1px"
          borderRadius="card"
          textAlign="left"
          _hover={{ boxShadow: "card", borderColor: "brand.emphasized" }}
          _focusWithin={{
            outline: "2px solid",
            outlineColor: "brand.focusRing",
            outlineOffset: "2px",
          }}
        >
          <Heading as="h3" fontFamily="heading" size="lg" fontWeight="600">
            <LinkOverlay asChild>
              <Link to="/trips/new" search={{ sample: sample.id }}>
                {sample.destination}
              </Link>
            </LinkOverlay>
          </Heading>
          <Text fontSize="sm" color="fg.muted">
            {sample.blurb}
          </Text>
          <Box mt="2" fontSize="xs" color="fg.muted" fontFamily="mono">
            {plural(sample.days, "day")} · {plural(sample.values.travelers, "traveler")}
          </Box>
        </LinkBox>
      ))}
    </SimpleGrid>
  )
}
