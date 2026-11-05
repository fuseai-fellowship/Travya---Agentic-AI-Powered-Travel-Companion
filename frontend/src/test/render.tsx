import { ChakraProvider } from "@chakra-ui/react"
import { type QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { type RenderOptions, render } from "@testing-library/react"
import type { ReactElement, ReactNode } from "react"
import { createQueryClient } from "@/app/queryClient"
import { system } from "@/theme/system"

function Wrapper({ children }: { children: ReactNode }) {
  return <ChakraProvider value={system}>{children}</ChakraProvider>
}

export function renderWithTheme(ui: ReactElement, options?: RenderOptions) {
  return render(ui, { wrapper: Wrapper, ...options })
}

function WithClient({ client, children }: { client: QueryClient; children: ReactNode }) {
  return (
    <ChakraProvider value={system}>
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    </ChakraProvider>
  )
}

/** Theme plus a fresh query client (no retries), for components that fetch. */
export function renderWithClient(ui: ReactElement, options?: RenderOptions) {
  const queryClient = createQueryClient()
  queryClient.setDefaultOptions({ queries: { retry: false, staleTime: 0 } })
  const result = render(ui, {
    wrapper: ({ children }) => <WithClient client={queryClient}>{children}</WithClient>,
    ...options,
  })
  return { queryClient, ...result }
}
