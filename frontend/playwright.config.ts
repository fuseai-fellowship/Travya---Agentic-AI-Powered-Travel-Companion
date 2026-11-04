import { defineConfig, devices } from "@playwright/test"

// PLAYWRIGHT_BASE_URL (compose e2e service) wins, then E2E_BASE_URL; empty values count as unset.
// With either set, the app is already running elsewhere, so no dev server is started here.
const externalBaseURL = process.env.PLAYWRIGHT_BASE_URL || process.env.E2E_BASE_URL || undefined
const baseURL = externalBaseURL ?? "http://localhost:5173"

export default defineConfig({
  testDir: "./e2e",
  // One worker: the specs share the demo's daily AI budget and the backend's per-user rate limits.
  workers: 1,
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  timeout: 120_000,
  expect: { timeout: 20_000 },
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : [["list"]],
  use: {
    baseURL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    {
      name: "mobile",
      use: { ...devices["Pixel 7"] },
      // The full journey runs on desktop; mobile covers navigation, layout and accessibility.
      grepInvert: /@desktop/,
    },
  ],
  webServer: externalBaseURL
    ? undefined
    : {
        command: "npm run dev",
        url: baseURL,
        reuseExistingServer: !process.env.CI,
        timeout: 120_000,
      },
})
