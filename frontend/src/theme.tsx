import { createSystem, defaultConfig } from "@chakra-ui/react"
import { buttonRecipe } from "./theme/button.recipe"

export const system = createSystem(defaultConfig, {
  globalCss: {
    html: {
      fontSize: "16px",
      colorScheme: "dark",
    },
    body: {
      fontSize: "0.875rem",
      margin: 0,
      padding: 0,
      bg: "black",
      color: "white",
    },
    ".main-link": {
      color: "ui.main",
      fontWeight: "bold",
    },
    // Force dark mode
    "*": {
      colorScheme: "dark !important",
    },
  },
  theme: {
    tokens: {
      colors: {
        ui: {
          main: { value: "#009688" },
        },
      },
    },
    recipes: {
      button: buttonRecipe,
    },
    semanticTokens: {
      colors: {
        "chakra-body-bg": { value: "#000000" },
        "chakra-body-text": { value: "#FFFFFF" },
        "chakra-subtle-bg": { value: "#1C1C1E" },
        "chakra-subtle-text": { value: "#EBEBF5" },
      },
    },
  },
})
