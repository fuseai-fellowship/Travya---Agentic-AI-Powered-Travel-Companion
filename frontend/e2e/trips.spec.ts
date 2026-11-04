import { expect, test } from "@playwright/test"
import { createDraftTrip, nav, startDemo } from "./support/app"

test.describe("trips", () => {
  test("validates the new-trip form like the API", async ({ page }) => {
    await startDemo(page)
    await page.goto("/trips/new")
    await page.getByRole("combobox", { name: "Destination" }).fill("Lisbon")
    await page.getByLabel("Start date").fill("2027-03-10")
    await page.getByLabel("End date").fill("2027-04-10")
    await page.getByRole("button", { name: "Plan my trip" }).click()
    await expect(page.getByText("Trips can be at most 21 days")).toBeVisible()
    await page.getByLabel("End date").fill("2027-03-01")
    await page.getByRole("button", { name: "Plan my trip" }).click()
    await expect(page.getByText("End date must be on or after the start date")).toBeVisible()
  })

  test("adds, edits and deletes an itinerary item on a draft", async ({ page }) => {
    await startDemo(page)
    await createDraftTrip(page, "kyoto")
    await page.getByRole("button", { name: "Add to day 1" }).click()
    await page.getByRole("textbox", { name: "Title" }).fill("Fushimi Inari at dawn")
    await page.getByRole("button", { name: "Add", exact: true }).click()
    await expect(page.getByText("Fushimi Inari at dawn")).toBeVisible()

    await page.getByRole("button", { name: "Edit Fushimi Inari at dawn" }).click()
    await page.getByRole("textbox", { name: "Title" }).fill("Fushimi Inari before sunrise")
    await page.getByRole("button", { name: "Save", exact: true }).click()
    await expect(page.getByText("Fushimi Inari before sunrise")).toBeVisible()

    await page.getByRole("button", { name: "Delete Fushimi Inari before sunrise" }).click()
    await page.getByRole("alertdialog").getByRole("button", { name: "Delete" }).click()
    await expect(page.getByText("Fushimi Inari before sunrise")).toHaveCount(0)
  })

  test("lists, searches and deletes trips", async ({ page }) => {
    await startDemo(page)
    await createDraftTrip(page, "lisbon")
    await nav(page, "Trips").click()
    await expect(page.getByRole("link", { name: "Lisbon" })).toBeVisible()

    await page.getByRole("searchbox", { name: "Search trips" }).fill("nowhere-at-all")
    await expect(page.getByText("No trips match")).toBeVisible()
    await page.getByRole("button", { name: "Clear filters" }).click()

    await page.getByRole("link", { name: "Lisbon" }).click()
    await page.getByRole("button", { name: "More trip actions" }).click()
    await page.getByRole("menuitem", { name: "Delete trip" }).click()
    await page.getByRole("alertdialog").getByRole("button", { name: "Delete trip" }).click()
    await expect(page).toHaveURL(/\/trips$/)
    await expect(page.getByText("Plan your first trip")).toBeVisible()
  })
})
