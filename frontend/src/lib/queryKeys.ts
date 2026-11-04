import type { Query, QueryClient } from "@tanstack/react-query"

/** Generated query keys look like `[{ _id: "tripsGetTrip", path: { trip_id }, query }]`. */
interface GeneratedKey {
  _id?: string
  path?: Record<string, unknown>
}

function keyOf(query: Query): GeneratedKey {
  const first = query.queryKey[0]
  return typeof first === "object" && first !== null ? (first as GeneratedKey) : {}
}

/** Invalidates every query generated for the given operation ids (e.g. "notesListNotes"). */
export function invalidateOperations(queryClient: QueryClient, ...ids: string[]) {
  return queryClient.invalidateQueries({
    predicate: (query) => ids.includes(keyOf(query)._id ?? ""),
  })
}

/** Everything about one trip (detail, itinerary, bookings, map, weather, photos) plus trip lists. */
export function invalidateTrip(queryClient: QueryClient, tripId: string) {
  return queryClient.invalidateQueries({
    predicate: (query) => {
      const key = keyOf(query)
      return key.path?.trip_id === tripId || key._id === "tripsListTrips"
    },
  })
}
