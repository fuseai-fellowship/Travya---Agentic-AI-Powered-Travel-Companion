import { createFileRoute } from "@tanstack/react-router"
import { z } from "zod"
import { TRIP_STATUSES } from "@/features/trips/status"
import { TripsPage } from "@/features/trips/TripsPage"

export const Route = createFileRoute("/_app/trips/")({
  validateSearch: z.object({
    q: z.string().max(100).optional().catch(undefined),
    status: z.enum(TRIP_STATUSES).optional().catch(undefined),
    page: z.number().int().min(1).optional().catch(undefined),
  }),
  component: TripsPage,
})
