import { createSystem, defaultConfig, defineConfig } from "@chakra-ui/react"

/**
 * Cartographic identity. Map paper and printed-map ink; the accents are the map's own day colours
 * (Okabe–Ito, colour-blind safe): route blue for actions, pin vermillion for places, bluish green
 * for "done". Contour lines are the only decoration. Text pairs meet WCAG AA (4.5:1) in both modes.
 *
 * Type: Overpass (an open Highway Gothic, i.e. road-sign lettering) for everything, Overpass Mono
 * for times, prices and codes, Noto Sans Devanagari for Nepali place names.
 *
 * Motion: one signature, used only for map things. Pins drop and routes draw, always with the
 * `map` easing and duration; nothing else fades or slides in. Off under prefers-reduced-motion.
 */
const SANS =
  "'Overpass Variable', 'Overpass Fallback', 'Noto Sans Devanagari Variable', ui-sans-serif, system-ui, sans-serif"

const config = defineConfig({
  globalCss: {
    "html, body": { bg: "bg", color: "fg" },
    body: { fontFeatureSettings: '"kern", "liga"', textRendering: "optimizeLegibility" },
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
      "pin-drop": {
        from: { opacity: 0, transform: "translateY(-12px)" },
        to: { opacity: 1, transform: "translateY(0)" },
      },
      "route-draw": {
        from: { strokeDashoffset: 1 },
        to: { strokeDashoffset: 0 },
      },
    },
    tokens: {
      fonts: {
        heading: { value: SANS },
        body: { value: SANS },
        mono: { value: "'Overpass Mono Variable', ui-monospace, SFMono-Regular, Menlo, monospace" },
        devanagari: { value: "'Noto Sans Devanagari Variable', 'Overpass Variable', sans-serif" },
      },
      colors: {
        paper: { value: "#F6F7F5" },
        ink: { value: "#102030" },
        night: { value: "#0C1722" },
        hairline: { value: "#D9DFDB" },
        brand: {
          50: { value: "#E6F2F9" },
          100: { value: "#C4E0F0" },
          200: { value: "#90C5E4" },
          300: { value: "#56A9D8" },
          400: { value: "#2A8EC7" },
          500: { value: "#0072B2" },
          600: { value: "#005F95" },
          700: { value: "#004C78" },
          800: { value: "#003A5C" },
          900: { value: "#002740" },
          950: { value: "#00182A" },
        },
        pin: {
          50: { value: "#FCEFE5" },
          100: { value: "#F8D8C0" },
          200: { value: "#F0B58A" },
          300: { value: "#F2964A" },
          400: { value: "#E27A26" },
          500: { value: "#D55E00" },
          600: { value: "#B34F00" },
          700: { value: "#A84800" },
          800: { value: "#6E2F00" },
          900: { value: "#401B00" },
          950: { value: "#241000" },
        },
        sea: {
          50: { value: "#E5F5F0" },
          100: { value: "#BFE7DA" },
          200: { value: "#86D3BB" },
          300: { value: "#3FC79D" },
          400: { value: "#1AAF84" },
          500: { value: "#009E73" },
          600: { value: "#008863" },
          700: { value: "#007A59" },
          800: { value: "#005640" },
          900: { value: "#003426" },
          950: { value: "#001D15" },
        },
      },
      radii: {
        card: { value: "8px" },
      },
      durations: {
        fast: { value: "150ms" },
        normal: { value: "200ms" },
        slow: { value: "250ms" },
        map: { value: "600ms" },
      },
      easings: {
        map: { value: "cubic-bezier(0.22, 1, 0.36, 1)" },
      },
    },
    semanticTokens: {
      colors: {
        bg: {
          DEFAULT: { value: { base: "{colors.paper}", _dark: "{colors.night}" } },
          subtle: { value: { base: "#EEF1EE", _dark: "#111D28" } },
          muted: { value: { base: "#E5E9E5", _dark: "#1B2A37" } },
          panel: { value: { base: "#FFFFFF", _dark: "#13202C" } },
          emphasized: { value: { base: "#D9DFDB", _dark: "#243545" } },
        },
        fg: {
          DEFAULT: { value: { base: "{colors.ink}", _dark: "#E5ECF1" } },
          muted: { value: { base: "#47566A", _dark: "#9FB0BE" } },
          subtle: { value: { base: "#5F6C7A", _dark: "#7F909E" } },
        },
        border: {
          DEFAULT: { value: { base: "{colors.hairline}", _dark: "#22323F" } },
          muted: { value: { base: "#E7EBE8", _dark: "#1A2733" } },
          emphasized: { value: { base: "#BCC6C0", _dark: "#34485A" } },
        },
        /** Contour hairlines: topographic brown on paper, faint blue-grey at night. */
        contour: {
          value: { base: "rgba(130, 98, 56, 0.30)", _dark: "rgba(150, 180, 205, 0.18)" },
        },
        brand: {
          solid: { value: { base: "{colors.brand.500}", _dark: "#56B4E9" } },
          contrast: { value: { base: "#FFFFFF", _dark: "{colors.night}" } },
          fg: { value: { base: "#00568A", _dark: "#7CC4EE" } }, // ≥4.5:1 over contour hairlines too
          muted: { value: { base: "{colors.brand.100}", _dark: "{colors.brand.900}" } },
          subtle: { value: { base: "{colors.brand.50}", _dark: "{colors.brand.950}" } },
          emphasized: { value: { base: "{colors.brand.200}", _dark: "{colors.brand.800}" } },
          focusRing: { value: { base: "{colors.brand.500}", _dark: "#56B4E9" } },
        },
        pin: {
          solid: { value: { base: "{colors.pin.500}", _dark: "{colors.pin.300}" } },
          contrast: { value: { base: "#FFFFFF", _dark: "{colors.night}" } },
          fg: { value: { base: "{colors.pin.700}", _dark: "{colors.pin.300}" } },
          muted: { value: { base: "{colors.pin.100}", _dark: "{colors.pin.900}" } },
          subtle: { value: { base: "{colors.pin.50}", _dark: "{colors.pin.950}" } },
          emphasized: { value: { base: "{colors.pin.200}", _dark: "{colors.pin.800}" } },
          focusRing: { value: { base: "{colors.pin.500}", _dark: "{colors.pin.300}" } },
        },
        sea: {
          solid: { value: { base: "{colors.sea.700}", _dark: "{colors.sea.300}" } },
          contrast: { value: { base: "#FFFFFF", _dark: "{colors.night}" } },
          fg: { value: { base: "{colors.sea.700}", _dark: "{colors.sea.300}" } },
          muted: { value: { base: "{colors.sea.100}", _dark: "{colors.sea.900}" } },
          subtle: { value: { base: "{colors.sea.50}", _dark: "{colors.sea.950}" } },
          emphasized: { value: { base: "{colors.sea.200}", _dark: "{colors.sea.800}" } },
          focusRing: { value: { base: "{colors.sea.500}", _dark: "{colors.sea.300}" } },
        },
      },
      shadows: {
        card: {
          value: {
            base: "0 1px 0 rgba(16, 32, 48, 0.04), 0 2px 8px rgba(16, 32, 48, 0.05)",
            _dark: "0 1px 2px rgba(0, 0, 0, 0.5)",
          },
        },
      },
    },
  },
})

export const system = createSystem(defaultConfig, config)
