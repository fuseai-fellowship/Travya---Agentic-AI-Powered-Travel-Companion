import { createFileRoute } from "@tanstack/react-router"
import { z } from "zod"
import { redirectIfSignedIn } from "@/features/auth/guard"
import { SignupPage } from "@/features/auth/SignupPage"

export const Route = createFileRoute("/signup")({
  validateSearch: z.object({ redirect: z.string().optional() }),
  beforeLoad: ({ context, search }) => redirectIfSignedIn(context.getUser, search.redirect),
  component: SignupPage,
})
