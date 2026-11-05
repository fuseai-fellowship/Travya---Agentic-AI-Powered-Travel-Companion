import { isRedirect } from "@tanstack/react-router"
import { describe, expect, it } from "vitest"
import { redirectIfSignedIn, requireUser, safeRedirect } from "./guard"

async function caught(promise: Promise<unknown>): Promise<unknown> {
  try {
    await promise
  } catch (error) {
    return error
  }
  return undefined
}

describe("requireUser", () => {
  it("sends signed-out visitors to /login with a return path", async () => {
    const error = await caught(requireUser(async () => null, "/trips/abc?tab=bookings"))
    expect(isRedirect(error)).toBe(true)
    expect((error as { options: unknown }).options).toMatchObject({
      to: "/login",
      search: { redirect: "/trips/abc?tab=bookings" },
    })
  })

  it("lets signed-in users through", async () => {
    await expect(requireUser(async () => ({ uid: "u1" }), "/trips")).resolves.toBeUndefined()
  })
})

describe("redirectIfSignedIn", () => {
  it("skips the sign-in page for signed-in users, to a safe target", async () => {
    const error = await caught(redirectIfSignedIn(async () => ({ uid: "u1" }), "//evil.example"))
    expect(isRedirect(error)).toBe(true)
    expect((error as { options: unknown }).options).toMatchObject({ href: "/trips" })
  })

  it("does nothing for visitors", async () => {
    await expect(redirectIfSignedIn(async () => null, "/notes")).resolves.toBeUndefined()
  })
})

describe("safeRedirect", () => {
  it("only allows same-site paths", () => {
    expect(safeRedirect("/assistant?c=1")).toBe("/assistant?c=1")
    expect(safeRedirect("https://evil.example")).toBe("/trips")
    expect(safeRedirect("//evil.example")).toBe("/trips")
    expect(safeRedirect("/\\evil.example")).toBe("/trips")
    expect(safeRedirect(undefined)).toBe("/trips")
  })
})
