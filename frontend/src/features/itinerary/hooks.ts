import { useMutation, useQueryClient } from "@tanstack/react-query"
import {
  tripsAddItineraryItemMutation,
  tripsDeleteItineraryItemMutation,
  tripsUpdateItineraryItemMutation,
} from "@/client/@tanstack/react-query.gen"
import { notifySuccess } from "@/lib/notify"
import { invalidateTrip } from "@/lib/queryKeys"

/** Item edits change the list, the map and the trip's budget numbers: refresh all of them. */
export function useItineraryMutations(tripId: string) {
  const queryClient = useQueryClient()
  const refresh = () => invalidateTrip(queryClient, tripId)

  const add = useMutation({
    ...tripsAddItineraryItemMutation(),
    meta: { errorTitle: "Couldn't add the item" },
    onSuccess: () => {
      notifySuccess("Added to the itinerary")
      return refresh()
    },
  })
  const update = useMutation({
    ...tripsUpdateItineraryItemMutation(),
    meta: { errorTitle: "Couldn't save the item" },
    onSuccess: () => refresh(),
  })
  const remove = useMutation({
    ...tripsDeleteItineraryItemMutation(),
    meta: { errorTitle: "Couldn't delete the item" },
    onSuccess: () => {
      notifySuccess("Removed from the itinerary")
      return refresh()
    },
  })
  return { add, update, remove }
}
