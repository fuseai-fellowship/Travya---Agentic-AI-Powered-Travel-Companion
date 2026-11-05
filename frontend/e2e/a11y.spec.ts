import { expect, test } from "@playwright/test"
import { createDraftTrip, expectAccessible, nav, startDemo } from "./support/app"

// No serious or critical axe violations on any top-level page, on desktop and mobile.
test.describe("accessibility", () => {
  test("landing page", async ({ page }) => {
    await page.goto("/")
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible()
    await expectAccessible(page)
  })

  test("signed-in pages", async ({ page }) => {
    await startDemo(page)
    await expect(page.getByText("Plan your first trip")).toBeVisible()
    await expectAccessible(page)

    await createDraftTrip(page)
    await expect(page.getByText("No itinerary yet")).toBeVisible()
    await expectAccessible(page)

    await nav(page, "Assistant").click()
    await expect(page.getByRole("heading", { name: "Ask the travel assistant" })).toBeVisible()
    await expectAccessible(page)

    await nav(page, "Notes").click()
    await expect(page.getByText("No notes yet")).toBeVisible()
    await expectAccessible(page)

    await nav(page, "Settings").click()
    await expect(page.getByRole("heading", { name: "Settings", level: 1 })).toBeVisible()
    await expect(page.getByText(/agent runs? left today/)).toBeVisible()
    await expectAccessible(page)
  })
})
