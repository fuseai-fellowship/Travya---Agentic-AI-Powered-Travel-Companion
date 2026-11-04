import { Alert, Heading, Stack, Text } from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { LuTicket } from "react-icons/lu"
import {
  tripsCancelBookingMutation,
  tripsConfirmBookingMutation,
  tripsListBookingsOptions,
} from "@/client/@tanstack/react-query.gen"
import type { BookingKind, BookingRead } from "@/client/types.gen"
import { ConfirmDialog } from "@/components/ConfirmDialog"
import { Empty, ErrorState, ListSkeleton } from "@/components/States"
import { formatMoney, toNumber } from "@/lib/format"
import { notifySuccess } from "@/lib/notify"
import { invalidateTrip } from "@/lib/queryKeys"
import { BookingCard } from "./BookingCard"

const GROUPS: Array<{ kind: BookingKind; title: string }> = [
  { kind: "flight", title: "Flights" },
  { kind: "hotel", title: "Stays" },
  { kind: "activity", title: "Activities" },
]

export function BookingsTab({ tripId }: { tripId: string }) {
  const queryClient = useQueryClient()
  const query = useQuery(tripsListBookingsOptions({ path: { trip_id: tripId } }))
  const [pending, setPending] = useState<{
    booking: BookingRead
    action: "confirm" | "cancel"
  } | null>(null)

  const confirm = useMutation({
    ...tripsConfirmBookingMutation(),
    meta: { errorTitle: "Couldn't confirm" },
    onSuccess: (booking) => {
      notifySuccess(
        "Booked (simulated)",
        `Confirmation code ${booking.confirmation_code ?? ""}`.trim(),
      )
      return invalidateTrip(queryClient, tripId)
    },
  })
  const cancel = useMutation({
    ...tripsCancelBookingMutation(),
    meta: { errorTitle: "Couldn't cancel" },
    onSuccess: () => {
      notifySuccess("Booking cancelled")
      return invalidateTrip(queryClient, tripId)
    },
  })

  if (query.isPending) return <ListSkeleton rows={3} height="120px" />
  if (query.isError)
    return (
      <ErrorState
        error={query.error}
        title="Couldn't load bookings"
        onRetry={() => query.refetch()}
      />
    )

  const run = () => {
    if (!pending) return
    const vars = { path: { trip_id: tripId, booking_id: pending.booking.id } }
    const mutation = pending.action === "confirm" ? confirm : cancel
    mutation.mutate(vars, { onSettled: () => setPending(null) })
  }

  return (
    <Stack gap="5">
      <Alert.Root status="info" borderRadius="card">
        <Alert.Indicator />
        <Alert.Title>Bookings are simulated. Nothing is reserved or charged.</Alert.Title>
      </Alert.Root>
      {query.data.length === 0 ? (
        <Empty
          icon={<LuTicket />}
          title="No quotes yet"
          description="The booking scout collects sample flight and stay quotes when the trip is planned. Add an origin to the trip for flights."
        />
      ) : (
        GROUPS.map(({ kind, title }) => {
          const items = query.data.filter((booking) => booking.kind === kind)
          if (!items.length) return null
          return (
            <Stack as="section" key={kind} gap="2" aria-label={title}>
              <Heading as="h3" size="md" fontFamily="heading">
                {title}
              </Heading>
              <Stack as="ul" gap="2">
                {items.map((booking) => (
                  <BookingCard
                    key={booking.id}
                    booking={booking}
                    onConfirm={(target) => setPending({ booking: target, action: "confirm" })}
                    onCancel={(target) => setPending({ booking: target, action: "cancel" })}
                  />
                ))}
              </Stack>
            </Stack>
          )
        })
      )}
      <ConfirmDialog
        open={pending !== null}
        onOpenChange={(open) => !open && setPending(null)}
        title={pending?.action === "cancel" ? "Cancel this booking?" : "Confirm this booking?"}
        description={
          pending?.action === "cancel" ? (
            <Text>The simulated booking “{pending.booking.title}” will be marked cancelled.</Text>
          ) : (
            <Stack gap="2">
              <Text>
                This is a <strong>simulated</strong> booking for the demo: Travya doesn't reserve or
                charge anything.
              </Text>
              {pending && (
                <Text>
                  {pending.booking.title} ·{" "}
                  <Text as="span" fontFamily="mono">
                    {formatMoney(toNumber(pending.booking.amount) ?? 0, pending.booking.currency)}
                  </Text>
                </Text>
              )}
            </Stack>
          )
        }
        confirmLabel={pending?.action === "cancel" ? "Cancel booking" : "Confirm (simulated)"}
        destructive={pending?.action === "cancel"}
        loading={confirm.isPending || cancel.isPending}
        onConfirm={run}
      />
    </Stack>
  )
}
