import { describe, expect, it } from "vitest"
import { emptyFormValues, SAMPLE_TRIPS, sampleFormValues } from "./samples"
import { type TripFormValues, toTripCreate, tripFormSchema } from "./tripSchema"

const valid: TripFormValues = {
  ...emptyFormValues(new Date(2026, 10, 5)),
  destination: "Kathmandu",
  start_date: "2026-12-01",
  end_date: "2026-12-05",
}

function errorsFor(values: Partial<TripFormValues>) {
  const result = tripFormSchema.safeParse({ ...valid, ...values })
  return result.success
    ? {}
    : Object.fromEntries(result.error.issues.map((issue) => [issue.path.join("."), issue.message]))
}

describe("tripFormSchema", () => {
  it("accepts a valid trip and every sample", () => {
    expect(tripFormSchema.safeParse(valid).success).toBe(true)
    for (const sample of SAMPLE_TRIPS) {
      expect(tripFormSchema.safeParse(sampleFormValues(sample)).success).toBe(true)
    }
  })

  it("requires the end date on or after the start date", () => {
    expect(errorsFor({ end_date: "2026-11-30" })).toEqual({
      end_date: "End date must be on or after the start date",
    })
  })

  it("allows at most 21 days, like the API", () => {
    expect(errorsFor({ end_date: "2026-12-21" })).toEqual({})
    expect(errorsFor({ end_date: "2026-12-22" })).toEqual({
      end_date: "Trips can be at most 21 days",
    })
  })

  it("checks travelers, currency, budget and destination", () => {
    expect(errorsFor({ travelers: 0 })).toHaveProperty("travelers")
    expect(errorsFor({ travelers: 21 })).toHaveProperty("travelers")
    expect(errorsFor({ travelers: 2.5 })).toHaveProperty("travelers")
    expect(errorsFor({ currency: "usd" })).toHaveProperty("currency")
    expect(errorsFor({ currency: "EURO" })).toHaveProperty("currency")
    expect(errorsFor({ budget: "12,50" })).toHaveProperty("budget")
    expect(errorsFor({ budget: "1250.50" })).toEqual({})
    expect(errorsFor({ destination: " K " })).toHaveProperty("destination")
  })
})

describe("toTripCreate", () => {
  it("fills the title and drops empty optionals", () => {
    expect(
      toTripCreate({ ...valid, title: " ", origin: "", budget: "", notes: "  " }),
    ).toMatchObject({
      title: "Trip to Kathmandu",
      origin: null,
      budget: null,
      notes: null,
      currency: "USD",
    })
  })
})
