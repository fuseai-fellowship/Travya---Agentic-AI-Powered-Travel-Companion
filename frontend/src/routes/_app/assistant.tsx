import { createFileRoute } from "@tanstack/react-router"
import { z } from "zod"
import { AssistantPage } from "@/features/assistant/AssistantPage"

export const Route = createFileRoute("/_app/assistant")({
  validateSearch: z.object({
    c: z.string().optional().catch(undefined),
    trip: z.string().optional().catch(undefined),
  }),
  component: AssistantPage,
})
