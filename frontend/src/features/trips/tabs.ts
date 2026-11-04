export const TRIP_TABS = [
  "itinerary",
  "bookings",
  "weather",
  "photos",
  "notes",
  "documents",
] as const
export type TripTab = (typeof TRIP_TABS)[number]

export const TAB_LABELS: Record<TripTab, string> = {
  itinerary: "Itinerary",
  bookings: "Bookings",
  weather: "Weather",
  photos: "Photos",
  notes: "Notes",
  documents: "Documents",
}
