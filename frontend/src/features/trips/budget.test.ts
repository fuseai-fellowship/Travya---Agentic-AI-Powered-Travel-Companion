import { describe, expect, it } from "vitest"
import type { BookingRead } from "@/client/types.gen"
import { computeBudget } from "./budget"

const booking = (overrides: Partial<BookingRead>): BookingRead => ({
  id: crypto.randomUUID(),
  trip_id: "t",
  kind: "hotel",
  title: "Hotel",
  provider: "Sample",
  details: {},
  amount: "100.00",
  currency: "USD",
  status: "quoted",
  confirmation_code: null,
  is_simulated: true,
  confirmed_at: null,
  created_at: "2026-11-01T00:00:00Z",
  ...overrides,
})

describe("computeBudget", () => {
  it("counts only confirmed bookings in the trip currency", () => {
    const summary = computeBudget({
      budget: "2000.00",
      currency: "USD",
      estimatedTotal: 1500,
      bookings: [
        booking({ amount: "450.50", status: "confirmed" }),
        booking({ amount: "300.25", status: "confirmed" }),
        booking({ amount: "999.00", status: "quoted" }),
        booking({ amount: "80.00", status: "cancelled" }),
        booking({ amount: "120.00", status: "confirmed", currency: "EUR" }),
      ],
    })
    expect(summary).toMatchObject({
      budget: 2000,
      planned: 1500,
      confirmed: 750.75,
      remaining: 1249.25,
      otherCurrencies: ["EUR"],
      plannedPct: 75,
      confirmedPct: 38,
      overBudget: false,
    })
  })

  it("flags a plan estimate above the budget and caps the percentage", () => {
    const summary = computeBudget({
      budget: 1000,
      currency: "EUR",
      estimatedTotal: 1400,
      bookings: [],
    })
    expect(summary.overBudget).toBe(true)
    expect(summary.plannedPct).toBe(100)
    expect(summary.confirmed).toBe(0)
  })

  it("never invents a budget", () => {
    const summary = computeBudget({
      budget: null,
      currency: "USD",
      estimatedTotal: null,
      bookings: [],
    })
    expect(summary).toMatchObject({
      budget: null,
      remaining: null,
      plannedPct: null,
      confirmedPct: null,
      overBudget: false,
    })
  })
})
