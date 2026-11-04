import { addDays, toDayString } from "@/lib/format"
import type { TripFormValues } from "./tripSchema"

export interface SampleTrip {
  id: string
  destination: string
  blurb: string
  days: number
  values: Omit<TripFormValues, "start_date" | "end_date" | "destination">
}

export const SAMPLE_TRIPS: SampleTrip[] = [
  {
    id: "kathmandu",
    destination: "Kathmandu",
    blurb: "Durbar squares, stupas and momos",
    days: 5,
    values: {
      title: "Kathmandu Valley temples and food",
      origin: "",
      travelers: 2,
      budget: "1500",
      currency: "USD",
      pace: "balanced",
      interests: ["culture", "food", "history"],
      notes: "Mix temple squares with local food; one sunrise viewpoint.",
    },
  },
  {
    id: "lisbon",
    destination: "Lisbon",
    blurb: "Miradouros, trams and pastéis",
    days: 4,
    values: {
      title: "Long weekend in Lisbon",
      origin: "",
      travelers: 2,
      budget: "1200",
      currency: "EUR",
      pace: "relaxed",
      interests: ["food", "viewpoints", "architecture"],
      notes: "",
    },
  },
  {
    id: "kyoto",
    destination: "Kyoto",
    blurb: "Shrines, gardens and tea houses",
    days: 6,
    values: {
      title: "Kyoto gardens and shrines",
      origin: "",
      travelers: 1,
      budget: "250000",
      currency: "JPY",
      pace: "balanced",
      interests: ["culture", "nature", "food"],
      notes: "Early starts to beat the crowds.",
    },
  },
]

/** Form values for a sample, starting a month from today. */
export function sampleFormValues(sample: SampleTrip, today: Date = new Date()): TripFormValues {
  const start = addDays(toDayString(today), 30)
  return {
    ...sample.values,
    destination: sample.destination,
    start_date: start,
    end_date: addDays(start, sample.days - 1),
  }
}

export function emptyFormValues(today: Date = new Date()): TripFormValues {
  const start = addDays(toDayString(today), 30)
  return {
    destination: "",
    title: "",
    origin: "",
    start_date: start,
    end_date: addDays(start, 4),
    travelers: 2,
    budget: "",
    currency: "USD",
    pace: "balanced",
    interests: [],
    notes: "",
  }
}
