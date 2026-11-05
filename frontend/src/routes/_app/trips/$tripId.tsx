import { createFileRoute } from "@tanstack/react-router"
import { z } from "zod"
import { TripPage } from "@/features/trips/TripPage"
import { TRIP_TABS } from "@/features/trips/tabs"

export const Route = createFileRoute("/_app/trips/$tripId")({
  validateSearch: z.object({
    tab: z.enum(TRIP_TABS).optional().catch(undefined),
  }),
  component: TripPage,
})
