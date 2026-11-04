import { Box, Heading, HStack, Image, LinkBox, LinkOverlay, Stack, Text } from "@chakra-ui/react"
import { Link } from "@tanstack/react-router"
import { LuUsers } from "react-icons/lu"
import type { TripRead } from "@/client/types.gen"
import { countdown, formatDateRange, plural, tripLength } from "@/lib/format"
import { StatusPill } from "./status"

export function TripRow({ trip }: { trip: TripRead }) {
  const length = tripLength(trip.start_date, trip.end_date)
  return (
    <LinkBox
      as="li"
      display="flex"
      gap={{ base: "3", md: "5" }}
      alignItems="center"
      p="3"
      bg="bg.panel"
      borderWidth="1px"
      borderRadius="card"
      transition="box-shadow 150ms ease-out, border-color 150ms ease-out"
      _hover={{ boxShadow: "card", borderColor: "border.emphasized" }}
      _focusWithin={{ outline: "2px solid", outlineColor: "brand.focusRing", outlineOffset: "2px" }}
    >
      <Box
        flexShrink={0}
        w={{ base: "72px", md: "132px" }}
        h={{ base: "72px", md: "88px" }}
        borderRadius="md"
        overflow="hidden"
        bg="brand.subtle"
      >
        {trip.cover_photo_url ? (
          <Image
            src={trip.cover_photo_url}
            alt=""
            width={264}
            height={176}
            loading="lazy"
            w="full"
            h="full"
            objectFit="cover"
          />
        ) : (
          <Box
            h="full"
            display="grid"
            placeItems="center"
            fontFamily="heading"
            fontSize="3xl"
            color="brand.fg"
            aria-hidden="true"
          >
            {trip.destination.charAt(0).toUpperCase()}
          </Box>
        )}
      </Box>
      <Stack gap="1" flex="1" minW="0">
        <HStack justify="space-between" align="start" gap="3">
          <Heading
            as="h2"
            fontFamily="heading"
            size={{ base: "lg", md: "xl" }}
            fontWeight="600"
            truncate
          >
            <LinkOverlay asChild>
              <Link to="/trips/$tripId" params={{ tripId: trip.id }}>
                {trip.destination}
              </Link>
            </LinkOverlay>
          </Heading>
          <StatusPill status={trip.status} />
        </HStack>
        <Text fontSize="sm" color="fg.muted" truncate>
          {trip.title}
        </Text>
        <HStack gap="3" fontSize="sm" color="fg.muted" flexWrap="wrap" rowGap="0">
          <Text>
            {formatDateRange(trip.start_date, trip.end_date)} · {plural(length, "day")}
          </Text>
          <Text color="brand.fg" fontWeight="500">
            {countdown(trip.start_date, trip.end_date)}
          </Text>
          <HStack gap="1">
            <LuUsers aria-hidden="true" />
            <Text>{plural(trip.travelers ?? 1, "traveler")}</Text>
          </HStack>
        </HStack>
      </Stack>
    </LinkBox>
  )
}
