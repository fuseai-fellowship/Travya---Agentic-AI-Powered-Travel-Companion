import { Heading, HStack, IconButton, Menu, Portal, Stack, Text } from "@chakra-ui/react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Link, useNavigate } from "@tanstack/react-router"
import { useState } from "react"
import { LuArrowLeft, LuEllipsisVertical, LuMessageCircle, LuTrash2, LuUsers } from "react-icons/lu"
import { tripsDeleteTripMutation } from "@/client/@tanstack/react-query.gen"
import type { TripDetail } from "@/client/types.gen"
import { ConfirmDialog } from "@/components/ConfirmDialog"
import { countdown, formatDateRange, plural, tripLength } from "@/lib/format"
import { notifySuccess } from "@/lib/notify"
import { invalidateOperations } from "@/lib/queryKeys"
import { BudgetMeter } from "./BudgetMeter"
import type { BudgetSummary } from "./budget"
import { ReplanDialog } from "./ReplanDialog"
import { StatusPill } from "./status"

export function TripHeader({
  trip,
  budget,
  planning,
  onReplan,
}: {
  trip: TripDetail
  budget: BudgetSummary
  planning: boolean
  onReplan: (instructions: string) => void
}) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [confirming, setConfirming] = useState(false)
  const remove = useMutation({
    ...tripsDeleteTripMutation(),
    meta: { errorTitle: "Couldn't delete the trip" },
    onSuccess: async () => {
      notifySuccess("Trip deleted")
      await invalidateOperations(queryClient, "tripsListTrips")
      await navigate({ to: "/trips" })
    },
  })

  return (
    <Stack gap="4" as="header">
      <HStack justify="space-between">
        <Link to="/trips" aria-label="Back to trips">
          <HStack gap="1" fontSize="sm" color="fg.muted" minH="44px">
            <LuArrowLeft aria-hidden="true" /> Trips
          </HStack>
        </Link>
        <HStack gap="2">
          <ReplanDialog disabled={planning} hasPlan={trip.plan !== null} onReplan={onReplan} />
          <Menu.Root positioning={{ placement: "bottom-end" }}>
            <Menu.Trigger asChild>
              <IconButton size="sm" variant="ghost" aria-label="More trip actions">
                <LuEllipsisVertical />
              </IconButton>
            </Menu.Trigger>
            <Portal>
              <Menu.Positioner>
                <Menu.Content>
                  <Menu.Item
                    value="ask"
                    onSelect={() => void navigate({ to: "/assistant", search: { trip: trip.id } })}
                  >
                    <LuMessageCircle /> Ask the assistant
                  </Menu.Item>
                  <Menu.Item value="delete" color="fg.error" onSelect={() => setConfirming(true)}>
                    <LuTrash2 /> Delete trip
                  </Menu.Item>
                </Menu.Content>
              </Menu.Positioner>
            </Portal>
          </Menu.Root>
        </HStack>
      </HStack>
      <Stack gap="1">
        <HStack gap="3" align="center" flexWrap="wrap">
          <Heading
            as="h1"
            fontFamily="heading"
            size={{ base: "3xl", md: "4xl" }}
            fontWeight="600"
            letterSpacing="-0.01em"
          >
            {trip.destination}
          </Heading>
          <StatusPill status={trip.status} />
        </HStack>
        <Text color="fg.muted">{trip.title}</Text>
        <HStack gap="3" fontSize="sm" color="fg.muted" flexWrap="wrap" rowGap="0">
          <Text>
            {formatDateRange(trip.start_date, trip.end_date)} ·{" "}
            {plural(tripLength(trip.start_date, trip.end_date), "day")}
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
      <BudgetMeter summary={budget} />
      <ConfirmDialog
        open={confirming}
        onOpenChange={setConfirming}
        title="Delete this trip?"
        description="The itinerary, quotes, bookings, photos, notes and documents for this trip are deleted. This can't be undone."
        confirmLabel="Delete trip"
        destructive
        loading={remove.isPending}
        onConfirm={() => remove.mutate({ path: { trip_id: trip.id } })}
      />
    </Stack>
  )
}
