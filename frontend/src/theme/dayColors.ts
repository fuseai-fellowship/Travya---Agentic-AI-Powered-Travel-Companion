/**
 * Okabe–Ito palette (colour-blind safe) for itinerary days. The day number is always printed on
 * markers and chips too, so colour is never the only cue.
 */
const OKABE_ITO = [
  { color: "#E69F00", text: "#1C1B19" },
  { color: "#56B4E9", text: "#1C1B19" },
  { color: "#009E73", text: "#1C1B19" },
  { color: "#F0E442", text: "#1C1B19" },
  { color: "#0072B2", text: "#FFFFFF" },
  { color: "#D55E00", text: "#1C1B19" },
  { color: "#CC79A7", text: "#1C1B19" },
  { color: "#000000", text: "#FFFFFF" },
] as const

export interface DayColor {
  color: string
  text: string
}

/** Colour for a 1-based day index; cycles after eight days. */
export function dayColor(dayIndex: number): DayColor {
  const index =
    (((Math.max(1, dayIndex) - 1) % OKABE_ITO.length) + OKABE_ITO.length) % OKABE_ITO.length
  return OKABE_ITO[index] ?? OKABE_ITO[0]
}
