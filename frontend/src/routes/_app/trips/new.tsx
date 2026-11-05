import { createFileRoute } from "@tanstack/react-router"
import { z } from "zod"
import { NewTripPage } from "@/features/trips/NewTripPage"

export const Route = createFileRoute("/_app/trips/new")({
  validateSearch: z.object({ sample: z.string().optional().catch(undefined) }),
  component: NewTripPage,
})
