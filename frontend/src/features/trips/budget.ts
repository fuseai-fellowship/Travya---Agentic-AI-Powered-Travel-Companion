import type { BookingRead } from "@/client/types.gen"
import { toNumber } from "@/lib/format"

export interface BudgetSummary {
  currency: string
  budget: number | null
  /** The planner's `estimated_total`, in the trip currency. */
  planned: number | null
  /** Confirmed (simulated) bookings in the trip currency. */
  confirmed: number
  /** Currencies of confirmed bookings that can't be added up without an exchange rate. */
  otherCurrencies: string[]
  remaining: number | null
  plannedPct: number | null
  confirmedPct: number | null
  overBudget: boolean
}

const pct = (value: number | null, of: number | null) =>
  value === null || of === null || of <= 0 ? null : Math.min(100, Math.round((value / of) * 100))

/** Only real numbers: the trip budget, the plan's estimate and confirmed bookings. No guesses. */
export function computeBudget(input: {
  budget: string | number | null | undefined
  currency: string
  estimatedTotal: number | null
  bookings: BookingRead[]
}): BudgetSummary {
  const budget = toNumber(input.budget)
  const confirmedBookings = input.bookings.filter((booking) => booking.status === "confirmed")
  let confirmed = 0
  const other = new Set<string>()
  for (const booking of confirmedBookings) {
    const amount = toNumber(booking.amount)
    if (amount === null) continue
    if (booking.currency === input.currency) confirmed += amount
    else other.add(booking.currency)
  }
  confirmed = Math.round(confirmed * 100) / 100
  const planned = input.estimatedTotal
  return {
    currency: input.currency,
    budget,
    planned,
    confirmed,
    otherCurrencies: [...other].sort(),
    remaining: budget === null ? null : Math.round((budget - confirmed) * 100) / 100,
    plannedPct: pct(planned, budget),
    confirmedPct: pct(confirmed, budget),
    overBudget: budget !== null && (confirmed > budget || (planned ?? 0) > budget),
  }
}
