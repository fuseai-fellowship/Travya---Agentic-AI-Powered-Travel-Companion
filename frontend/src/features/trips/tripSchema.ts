import { z } from "zod"
import type { TripCreate } from "@/client/types.gen"
import { daysBetween } from "@/lib/format"

/** Mirrors backend `app/schemas/trips.py` so most mistakes are caught before a round trip. */
export const MAX_TRIP_DAYS = 21
const DAY = /^\d{4}-\d{2}-\d{2}$/

export const PACES = ["relaxed", "balanced", "packed"] as const

export const INTERESTS = [
  "culture",
  "food",
  "nature",
  "history",
  "art",
  "architecture",
  "viewpoints",
  "nightlife",
  "shopping",
  "adventure",
  "relaxation",
  "family",
] as const

export const tripFormSchema = z
  .object({
    destination: z
      .string()
      .trim()
      .min(2, "Enter a destination")
      .max(200, "Use at most 200 characters"),
    title: z.string().trim().max(200, "Use at most 200 characters"),
    origin: z.string().trim().max(200, "Use at most 200 characters"),
    start_date: z.string().regex(DAY, "Pick a start date"),
    end_date: z.string().regex(DAY, "Pick an end date"),
    travelers: z
      .number({ error: "Enter the number of travelers" })
      .int("Use a whole number")
      .min(1, "At least 1 traveler")
      .max(20, "At most 20 travelers"),
    budget: z
      .string()
      .trim()
      .refine(
        (value) => value === "" || /^\d+(\.\d{1,2})?$/.test(value),
        "Enter an amount like 1500",
      ),
    currency: z.string().regex(/^[A-Z]{3}$/, "Use a 3-letter code like USD"),
    pace: z.enum(PACES),
    interests: z.array(z.string()).max(8, "Pick up to 8 interests"),
    notes: z.string().max(2000, "Use at most 2000 characters"),
  })
  .superRefine((values, ctx) => {
    if (!DAY.test(values.start_date) || !DAY.test(values.end_date)) return
    const span = daysBetween(values.start_date, values.end_date)
    if (span < 0) {
      ctx.addIssue({
        code: "custom",
        path: ["end_date"],
        message: "End date must be on or after the start date",
      })
    } else if (span + 1 > MAX_TRIP_DAYS) {
      ctx.addIssue({
        code: "custom",
        path: ["end_date"],
        message: `Trips can be at most ${MAX_TRIP_DAYS} days`,
      })
    }
  })

export type TripFormValues = z.infer<typeof tripFormSchema>

export function toTripCreate(values: TripFormValues): TripCreate {
  const destination = values.destination.trim()
  return {
    title: values.title.trim() || `Trip to ${destination}`,
    destination,
    origin: values.origin.trim() || null,
    start_date: values.start_date,
    end_date: values.end_date,
    travelers: values.travelers,
    budget: values.budget.trim() ? values.budget.trim() : null,
    currency: values.currency,
    pace: values.pace,
    interests: values.interests,
    notes: values.notes.trim() || null,
  }
}
