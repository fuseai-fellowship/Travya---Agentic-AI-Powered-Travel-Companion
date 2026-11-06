import { describe, expect, it, vi } from "vitest"
import { RELOAD_FLAG, recoverFromStaleChunks } from "./staleChunks"

describe("recoverFromStaleChunks", () => {
  it("reloads once when a lazy chunk from an old deploy is gone", () => {
    const target = new EventTarget() as unknown as Window
    Object.assign(target, { setTimeout: vi.fn() })
    sessionStorage.clear()
    const reload = vi.fn()
    recoverFromStaleChunks(target, sessionStorage, reload)

    const first = new Event("vite:preloadError", { cancelable: true })
    target.dispatchEvent(first)
    expect(reload).toHaveBeenCalledOnce()
    expect(first.defaultPrevented).toBe(true)
    expect(sessionStorage.getItem(RELOAD_FLAG)).toBe("1")

    // Still failing after the reload: let the error boundary show it instead of looping.
    const second = new Event("vite:preloadError", { cancelable: true })
    target.dispatchEvent(second)
    expect(reload).toHaveBeenCalledOnce()
    expect(second.defaultPrevented).toBe(false)
  })
})
