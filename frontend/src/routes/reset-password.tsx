import { createFileRoute } from "@tanstack/react-router"
import { z } from "zod"
import { ResetPasswordPage } from "@/features/auth/ResetPasswordPage"

export const Route = createFileRoute("/reset-password")({
  validateSearch: z.object({ oobCode: z.string().optional(), mode: z.string().optional() }),
  component: ResetPasswordPage,
})
