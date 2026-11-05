import { createFileRoute } from "@tanstack/react-router"
import { requireUser } from "@/features/auth/guard"
import { AppShell } from "@/features/shell/AppShell"

export const Route = createFileRoute("/_app")({
  beforeLoad: ({ context, location }) => requireUser(context.getUser, location.href),
  component: AppShell,
})
