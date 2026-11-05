import { createSystem, defaultConfig, defineConfig } from "@chakra-ui/react"

/**
 * Warm paper and ink, a saffron/terracotta accent (a prayer-flag nod) and a deep teal.
 * `brand.solid` is darker than the #E4572E accent so white button text keeps 4.5:1 contrast.
 */
const config = defineConfig({
  globalCss: {
    "html, body": { bg: "bg", color: "fg" },
    body: { fontFeatureSettings: '"ss01"' },
    "*:focus-visible": { outlineColor: "brand.focusRing" },
    "*, *::before, *::after": {
      _motionReduce: {
        animationDuration: "0.01ms !important",
        animationIterationCount: "1 !important",
        transitionDuration: "0.01ms !important",
        scrollBehavior: "auto !important",
      },
    },
  },
  theme: {
    keyframes: {
      "travya-pulse": {
        "0%, 80%, 100%": { opacity: 0.25 },
        "40%": { opacity: 1 },
      },
    },
    tokens: {
      fonts: {
        heading: { value: "'Fraunces Variable', Georgia, 'Times New Roman', serif" },
        body: { value: "'Geist Variable', ui-sans-serif, system-ui, sans-serif" },
        mono: { value: "'Geist Mono Variable', ui-monospace, SFMono-Regular, Menlo, monospace" },
      },
      colors: {
        paper: { value: "#FBF8F3" },
        ink: { value: "#1C1B19" },
        hairline: { value: "#E8E2D8" },
        brand: {
          50: { value: "#FDF1EC" },
          100: { value: "#FADCD0" },
          200: { value: "#F5B8A1" },
          300: { value: "#EE8E6F" },
          400: { value: "#E86F4A" },
          500: { value: "#E4572E" },
          600: { value: "#C4441F" },
          700: { value: "#B23C1A" },
          800: { value: "#7E2B13" },
          900: { value: "#4F1B0C" },
          950: { value: "#2C0F07" },
        },
        sea: {
          50: { value: "#E7F4F4" },
          100: { value: "#C3E4E3" },
          200: { value: "#8ECCCA" },
          300: { value: "#55AFAD" },
          400: { value: "#2A9594" },
          500: { value: "#0E7C7B" },
          600: { value: "#0B6766" },
          700: { value: "#095453" },
          800: { value: "#073E3D" },
          900: { value: "#042827" },
          950: { value: "#021514" },
        },
      },
      radii: {
        card: { value: "10px" },
      },
      durations: {
        fast: { value: "150ms" },
        normal: { value: "200ms" },
        slow: { value: "250ms" },
      },
    },
    semanticTokens: {
      colors: {
        bg: {
          DEFAULT: { value: { base: "{colors.paper}", _dark: "#151412" } },
          subtle: { value: { base: "#F4EFE7", _dark: "#1C1B18" } },
          muted: { value: { base: "#EFE8DD", _dark: "#25231F" } },
          panel: { value: { base: "#FFFFFF", _dark: "#1E1D1A" } },
          emphasized: { value: { base: "#E8E2D8", _dark: "#2E2B27" } },
        },
        fg: {
          DEFAULT: { value: { base: "{colors.ink}", _dark: "#F3EFE8" } },
          muted: { value: { base: "#6B665E", _dark: "#B5AFA4" } },
          subtle: { value: { base: "#8A847A", _dark: "#8F897F" } },
        },
        border: {
          DEFAULT: { value: { base: "{colors.hairline}", _dark: "#34312C" } },
          muted: { value: { base: "#F0EBE3", _dark: "#2A2824" } },
          emphasized: { value: { base: "#D6CEC1", _dark: "#46423B" } },
        },
        brand: {
          solid: { value: { base: "{colors.brand.600}", _dark: "#F07450" } },
          contrast: { value: { base: "#FFFFFF", _dark: "{colors.ink}" } },
          fg: { value: { base: "{colors.brand.700}", _dark: "{colors.brand.300}" } },
          muted: { value: { base: "{colors.brand.100}", _dark: "{colors.brand.900}" } },
          subtle: { value: { base: "{colors.brand.50}", _dark: "{colors.brand.950}" } },
          emphasized: { value: { base: "{colors.brand.200}", _dark: "{colors.brand.800}" } },
          focusRing: { value: { base: "{colors.brand.500}", _dark: "{colors.brand.400}" } },
          accent: { value: { base: "{colors.brand.500}", _dark: "{colors.brand.400}" } },
        },
        sea: {
          solid: { value: { base: "{colors.sea.500}", _dark: "{colors.sea.300}" } },
          contrast: { value: { base: "#FFFFFF", _dark: "{colors.ink}" } },
          fg: { value: { base: "{colors.sea.600}", _dark: "{colors.sea.200}" } },
          muted: { value: { base: "{colors.sea.100}", _dark: "{colors.sea.900}" } },
          subtle: { value: { base: "{colors.sea.50}", _dark: "{colors.sea.950}" } },
          emphasized: { value: { base: "{colors.sea.200}", _dark: "{colors.sea.800}" } },
          focusRing: { value: { base: "{colors.sea.500}", _dark: "{colors.sea.300}" } },
        },
      },
      shadows: {
        card: {
          value: {
            base: "0 1px 2px rgba(28, 27, 25, 0.06), 0 4px 12px rgba(28, 27, 25, 0.05)",
            _dark: "0 1px 2px rgba(0, 0, 0, 0.4)",
          },
        },
      },
    },
  },
})

export const system = createSystem(defaultConfig, config)
