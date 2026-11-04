import { ChakraProvider } from "@chakra-ui/react"
import { type RenderOptions, render } from "@testing-library/react"
import type { ReactElement, ReactNode } from "react"
import { system } from "@/theme/system"

function Wrapper({ children }: { children: ReactNode }) {
  return <ChakraProvider value={system}>{children}</ChakraProvider>
}

export function renderWithTheme(ui: ReactElement, options?: RenderOptions) {
  return render(ui, { wrapper: Wrapper, ...options })
}
