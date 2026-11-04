import { expect, test } from "@playwright/test"
import { nav, startDemo } from "./support/app"
import { createEmulatorUser, uniqueEmail } from "./support/env"

test.describe("authentication", () => {
  test("protected pages send visitors to sign in and back", async ({ page }) => {
    await page.goto("/notes")
    await expect(page).toHaveURL(/\/login\?redirect=%2Fnotes/)
    await expect(page.getByRole("heading", { name: "Welcome Back" })).toBeVisible()
  })

  test("signs up with email, signs out and signs back in", async ({ page }) => {
    const email = uniqueEmail("signup")
    const password = "correct-horse-battery"

    await page.goto("/signup")
    await page.getByRole("textbox", { name: "Full name" }).fill("Ada Traveller")
    await page.getByRole("textbox", { name: "Email" }).fill(email)
    await page.getByLabel("Password", { exact: true }).fill(password)
    await page.getByLabel("Confirm password").fill(password)
    await page.getByRole("button", { name: "Create account" }).click()
    await expect(page).toHaveURL(/\/trips$/)

    await page.getByRole("button", { name: /^Account menu for / }).click()
    await page.getByRole("menuitem", { name: "Sign out" }).click()
    await expect(page).toHaveURL(/\/$/)

    await page.goto("/login")
    await page.getByRole("textbox", { name: "Email" }).fill(email)
    await page.getByLabel("Password", { exact: true }).fill(password)
    await page.getByRole("button", { name: "Sign In" }).click()
    await expect(page).toHaveURL(/\/trips$/)
  })

  test("shows a friendly error for a wrong password", async ({ page }) => {
    const email = uniqueEmail("wrong")
    await createEmulatorUser(email, "right-password-123")
    await page.goto("/login")
    await page.getByRole("textbox", { name: "Email" }).fill(email)
    await page.getByLabel("Password", { exact: true }).fill("wrong-password-123")
    await page.getByRole("button", { name: "Sign In" }).click()
    await expect(page.getByText("That email and password don't match an account.")).toBeVisible()
  })

  test("requests a password reset", async ({ page }) => {
    await page.goto("/reset-password")
    await page.getByRole("textbox", { name: "Email" }).fill(uniqueEmail("reset"))
    await page.getByRole("button", { name: "Send reset link" }).click()
    await expect(page.getByText("Check your inbox")).toBeVisible()
  })

  test("upgrades a demo account to email and keeps it", async ({ page }) => {
    await startDemo(page)
    await nav(page, "Settings").click()
    await expect(page.getByText("You're using a demo account")).toBeVisible()
    await page.getByRole("textbox", { name: "Email" }).fill(uniqueEmail("upgrade"))
    await page.getByLabel("Password", { exact: true }).fill("upgrade-password-123")
    await page.getByRole("button", { name: "Save with email" }).click()
    await expect(page.getByText(/^Signed in as/)).toBeVisible()
  })
})
