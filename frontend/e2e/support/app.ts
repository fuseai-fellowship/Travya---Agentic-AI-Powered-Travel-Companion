import AxeBuilder from "@axe-core/playwright"
import { expect, type Page } from "@playwright/test"

/** Signs in through "Try the demo" (Firebase anonymous auth) and waits for the trips page. */
export async function startDemo(page: Page) {
  await page.goto("/")
  await page.getByRole("button", { name: "Try the demo, no signup" }).first().click()
  await expect(page).toHaveURL(/\/trips$/)
}

/** Creates a draft trip from a sample without starting the agents (no AI budget used). */
export async function createDraftTrip(page: Page, sample = "lisbon") {
  await page.goto(`/trips/new?sample=${sample}`)
  await page.getByRole("button", { name: "Save as draft" }).click()
  await expect(page).toHaveURL(/\/trips\/[0-9a-f-]{36}/)
  return page.url()
}

/** Main navigation: the sidebar on desktop, the bottom tab bar on mobile. */
export function nav(page: Page, name: "Trips" | "Assistant" | "Notes" | "Settings") {
  return page.getByRole("navigation", { name: "Main" }).getByRole("link", { name, exact: true })
}

/** WCAG 2.2 AA scan; serious and critical violations fail the test. */
export async function expectAccessible(page: Page) {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
    // Third-party map controls are outside our markup; the itinerary list is the accessible equivalent.
    .exclude(".maplibregl-control-container")
    .analyze()
  const blocking = results.violations.filter(
    (violation) => violation.impact === "serious" || violation.impact === "critical",
  )
  expect(
    blocking.map((violation) => ({
      id: violation.id,
      impact: violation.impact,
      targets: violation.nodes.map((node) => node.target.join(" ")).slice(0, 5),
    })),
  ).toEqual([])
}
