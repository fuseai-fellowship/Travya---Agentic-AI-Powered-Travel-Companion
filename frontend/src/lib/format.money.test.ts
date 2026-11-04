import { describe, expect, it } from "vitest"
import { formatMoney } from "./format"

describe("formatMoney", () => {
  it("shows cents only when there are some", () => {
    expect(formatMoney(516.8, "USD")).toMatch(/516\.80/)
    expect(formatMoney(25, "USD")).not.toMatch(/\./)
  })

  it("drops cents for large and compact amounts", () => {
    expect(formatMoney(1500.5, "USD")).not.toMatch(/\.\d/)
    expect(formatMoney(12.34, "USD", { compact: true })).not.toMatch(/\.\d/)
  })

  it("falls back for unknown currency codes", () => {
    expect(formatMoney(10, "ZZZZ")).toBe("10 ZZZZ")
  })
})
