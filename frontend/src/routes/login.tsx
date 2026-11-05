import { createFileRoute } from "@tanstack/react-router"
import { z } from "zod"
import { redirectIfSignedIn } from "@/features/auth/guard"
import { LoginPage } from "@/features/auth/LoginPage"

export const Route = createFileRoute("/login")({
  validateSearch: z.object({ redirect: z.string().optional() }),
  beforeLoad: ({ context, search }) => redirectIfSignedIn(context.getUser, search.redirect),
  component: LoginPage,
})
