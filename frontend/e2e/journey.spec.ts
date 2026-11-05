import { expect, test } from "@playwright/test"
import { nav, startDemo } from "./support/app"

// The recruiter path from the design brief: demo → sample trip → watch the agents → itinerary and
// map → confirm a simulated booking → ask the assistant → notes. Runs against the full stack
// (backend with OFFLINE_INTEGRATIONS=true and the Firebase Auth emulator).
test.describe("demo journey @desktop", () => {
  test.describe.configure({ timeout: 180_000 })

  test("plans a sample trip and uses every area of the app", async ({ page }) => {
    await test.step("start the demo without signing up", async () => {
      await startDemo(page)
      await expect(page.getByText("Plan your first trip")).toBeVisible()
    })

    await test.step("plan the Kathmandu sample and watch the agents", async () => {
      await page.getByRole("link", { name: "Kathmandu" }).click()
      await expect(page.getByRole("combobox", { name: "Destination" })).toHaveValue("Kathmandu")
      await page.getByRole("button", { name: "Plan my trip" }).click()

      await expect(page).toHaveURL(/\/trips\/[0-9a-f-]{36}$/)
      await expect(page.getByRole("heading", { level: 1, name: "Kathmandu" })).toBeVisible()
      await expect(page.getByText(/itinerary is ready/).first()).toBeVisible({ timeout: 120_000 })
    })

    await test.step("see the itinerary and the map", async () => {
      await expect(page.getByRole("heading", { level: 3, name: /^Day 1 ·/ })).toBeVisible()
      await expect(page.getByRole("button", { name: "Day 1", exact: true })).toBeVisible()
      await expect(page.locator(".maplibregl-canvas")).toBeVisible()
      await expect(page.getByRole("button", { name: /^Day 1, stop 1:/ })).toBeVisible()
      await expect(page.getByRole("meter", { name: "Budget used" })).toBeVisible()
    })

    await test.step("confirm a simulated booking", async () => {
      await page.getByRole("tab", { name: "Bookings" }).click()
      await expect(
        page.getByText("Bookings are simulated. Nothing is reserved or charged."),
      ).toBeVisible()
      await page.getByRole("button", { name: "Confirm booking" }).first().click()
      const dialog = page.getByRole("dialog", { name: "Confirm this booking?" })
      await expect(dialog).toContainText("simulated")
      await dialog.getByRole("button", { name: "Confirm (simulated)" }).click()
      await expect(page.getByRole("button", { name: "Cancel booking" }).first()).toBeVisible()
      await expect(page.getByText(/^Code/).first()).toBeVisible()
    })

    await test.step("ask the assistant", async () => {
      await nav(page, "Assistant").click()
      const composer = page.getByRole("textbox", { name: "Message the travel assistant" })
      await composer.fill("What should I pack for Kathmandu?")
      await composer.press("Enter")
      const log = page.getByRole("log", { name: "Conversation" })
      await expect(log).toContainText("What should I pack for Kathmandu?")
      // Feedback buttons appear once the streamed reply has been saved.
      await expect(log.getByRole("button", { name: "Helpful answer", exact: true })).toBeVisible({
        timeout: 60_000,
      })
    })

    await test.step("create, edit and delete a note", async () => {
      await nav(page, "Notes").click()
      await page.getByRole("button", { name: "New note" }).click()
      let dialog = page.getByRole("dialog", { name: "New note" })
      await dialog.getByRole("textbox", { name: "Title" }).fill("Bring a headlamp")
      await dialog
        .getByRole("textbox", { name: "Note (Markdown)" })
        .fill("Power cuts happen. **Pack one.**")
      await dialog.getByRole("button", { name: "Save note" }).click()
      await expect(
        page.getByRole("button", { name: "Bring a headlamp", exact: true }),
      ).toBeVisible()

      await page.getByRole("button", { name: "Bring a headlamp", exact: true }).click()
      dialog = page.getByRole("dialog", { name: "Edit note" })
      await dialog.getByRole("textbox", { name: "Title" }).fill("Bring two headlamps")
      await dialog.getByRole("button", { name: "Save note" }).click()
      await expect(
        page.getByRole("button", { name: "Bring two headlamps", exact: true }),
      ).toBeVisible()

      await page.getByRole("button", { name: "Bring two headlamps", exact: true }).click()
      await page
        .getByRole("dialog", { name: "Edit note" })
        .getByRole("button", { name: "Delete" })
        .click()
      await page
        .getByRole("alertdialog", { name: "Delete this note?" })
        .getByRole("button", { name: "Delete" })
        .click()
      await expect(
        page.getByRole("button", { name: "Bring two headlamps", exact: true }),
      ).toHaveCount(0)
      await expect(page.getByText("No notes yet")).toBeVisible()
    })
  })
})
