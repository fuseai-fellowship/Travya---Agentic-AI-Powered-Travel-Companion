import { act, screen } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"
import { resetWake, wakeServer } from "@/lib/wake"
import { renderWithClient } from "@/test/render"
import { WakeBanner } from "./WakeBanner"

vi.mock("@/lib/firebase", async () => (await import("@/test/sse")).firebaseMock)

afterEach(() => resetWake())

describe("WakeBanner", () => {
  it("says the free server is waking instead of offline, then disappears", async () => {
    let live: () => void = () => undefined
    const ready = new Promise<void>((resolve) => {
      live = resolve
    })
    renderWithClient(<WakeBanner />)
    expect(screen.queryByText(/Waking up/)).not.toBeInTheDocument()

    let waking: Promise<boolean> = Promise.resolve(false)
    act(() => {
      waking = wakeServer({
        healthUrl: "http://api.test/health",
        fetch: (async () => {
          await ready
          return new Response("ok")
        }) as unknown as typeof fetch,
      })
    })
    expect(await screen.findByText("Waking up the free server…")).toBeInTheDocument()
    expect(screen.getByRole("status")).toHaveTextContent(/takes up to a minute/)

    await act(async () => {
      live()
      await waking
    })
    expect(screen.queryByText(/Waking up/)).not.toBeInTheDocument()
  })
})
