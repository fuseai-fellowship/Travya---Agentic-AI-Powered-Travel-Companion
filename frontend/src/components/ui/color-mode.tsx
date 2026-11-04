import { IconButton, type IconButtonProps } from "@chakra-ui/react"
import { ThemeProvider, useTheme } from "next-themes"
import type { ReactNode } from "react"
import { LuMoon, LuSun } from "react-icons/lu"

export function ColorModeProvider({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider attribute="class" defaultTheme="light" enableSystem disableTransitionOnChange>
      {children}
    </ThemeProvider>
  )
}

export type ColorMode = "light" | "dark"

export function useColorMode() {
  const { resolvedTheme, setTheme, theme } = useTheme()
  const colorMode: ColorMode = resolvedTheme === "dark" ? "dark" : "light"
  return {
    colorMode,
    preference: theme ?? "light",
    setColorMode: setTheme,
    toggleColorMode: () => setTheme(colorMode === "dark" ? "light" : "dark"),
  }
}

export function ColorModeButton(props: Omit<IconButtonProps, "aria-label">) {
  const { colorMode, toggleColorMode } = useColorMode()
  const next = colorMode === "dark" ? "light" : "dark"
  return (
    <IconButton
      variant="ghost"
      aria-label={`Switch to ${next} mode`}
      onClick={toggleColorMode}
      {...props}
    >
      {colorMode === "dark" ? <LuSun /> : <LuMoon />}
    </IconButton>
  )
}
