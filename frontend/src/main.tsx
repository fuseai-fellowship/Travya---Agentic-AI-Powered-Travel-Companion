import "@fontsource-variable/fraunces"
import "@fontsource-variable/geist"
import "@fontsource-variable/geist-mono"

import { RouterProvider } from "@tanstack/react-router"
import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import { Providers } from "@/app/providers"
import { createQueryClient } from "@/app/queryClient"
import { createAppRouter } from "@/app/router"
import { setupApiClient } from "@/lib/api"
import { currentUser } from "@/lib/firebase"
import { recoverFromStaleChunks } from "@/lib/staleChunks"

setupApiClient()
recoverFromStaleChunks()

const queryClient = createQueryClient()
const router = createAppRouter({ queryClient, getUser: currentUser })

const root = document.getElementById("root")
if (!root) throw new Error("Missing #root element")

createRoot(root).render(
  <StrictMode>
    <Providers queryClient={queryClient}>
      <RouterProvider router={router} />
    </Providers>
  </StrictMode>,
)
