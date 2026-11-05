import { ChakraProvider } from "@chakra-ui/react"
import { type QueryClient, QueryClientProvider } from "@tanstack/react-query"
import type { ReactNode } from "react"
import { ColorModeProvider } from "@/components/ui/color-mode"
import { Toaster } from "@/components/ui/toaster"
import { AuthProvider } from "@/features/auth/AuthProvider"
import { system } from "@/theme/system"

export function Providers({
  queryClient,
  children,
}: {
  queryClient: QueryClient
  children: ReactNode
}) {
  return (
    <ChakraProvider value={system}>
      <ColorModeProvider>
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            {children}
            <Toaster />
          </AuthProvider>
        </QueryClientProvider>
      </ColorModeProvider>
    </ChakraProvider>
  )
}
