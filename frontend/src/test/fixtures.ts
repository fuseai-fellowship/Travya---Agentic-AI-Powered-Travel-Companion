import type {
  BookingRead,
  ConversationRead,
  ItineraryItemRead,
  MeRead,
  NoteRead,
  TripDetail,
  TripMap,
} from "@/client/types.gen"

export const TRIP_ID = "7d1f3c2a-1111-4222-8333-944455566677"

export const trip: TripDetail = {
  id: TRIP_ID,
  title: "Kathmandu Valley temples and food",
  destination: "Kathmandu",
  origin: null,
  start_date: "2026-12-01",
  end_date: "2026-12-03",
  travelers: 2,
  budget: "1500.00",
  currency: "USD",
  pace: "balanced",
  interests: ["culture", "food"],
  notes: null,
  country_code: "NP",
  latitude: 27.7172,
  longitude: 85.324,
  status: "planned",
  cover_photo_url: null,
  planned_at: "2026-11-05T10:00:00Z",
  created_at: "2026-11-05T09:00:00Z",
  updated_at: "2026-11-05T10:00:00Z",
  plan: {
    summary: "Three easy days of temple squares and food.",
    days: [{ date: "2026-12-01", theme: "Old Kathmandu", activities: [] }],
    estimated_total: 900,
    budget_breakdown: { food: 200, lodging: 500 },
    packing_tips: ["Layers for cool mornings"],
    local_tips: ["Walk clockwise around stupas"],
    sources: [
      { title: "Wikivoyage travel guide", url: "https://en.wikivoyage.org/wiki/Kathmandu" },
    ],
  },
}

export const items: ItineraryItemRead[] = [
  {
    id: "item-1",
    trip_id: TRIP_ID,
    day: "2026-12-01",
    position: 0,
    start_time: "09:00:00",
    end_time: "11:00:00",
    title: "Kathmandu Durbar Square",
    description: "Palaces and courtyards.",
    category: "sight",
    place_name: "Kathmandu Durbar Square",
    latitude: 27.7045,
    longitude: 85.3077,
    estimated_cost: "15.00",
    source: "agent",
  },
]

export const bookings: BookingRead[] = [
  {
    id: "booking-1",
    trip_id: TRIP_ID,
    kind: "hotel",
    title: "Hotel Thamel, 2 nights",
    provider: "Sample stays",
    details: { nights: 2, rating: 4.5 },
    amount: "240.00",
    currency: "USD",
    status: "quoted",
    confirmation_code: null,
    is_simulated: true,
    confirmed_at: null,
    created_at: "2026-11-05T10:00:00Z",
  },
]

export const tripMap: TripMap = {
  type: "FeatureCollection",
  trip_id: TRIP_ID,
  center: [85.324, 27.7172],
  bbox: [85.3, 27.7, 85.33, 27.72],
  attribution: "© OpenStreetMap contributors",
  features: [
    {
      type: "Feature",
      geometry: { type: "Point", coordinates: [85.3077, 27.7045] },
      properties: {
        kind: "stop",
        item_id: "item-1",
        title: "Kathmandu Durbar Square",
        day_index: 1,
        day: "2026-12-01",
      },
    },
  ],
}

export const me: MeRead = {
  id: "user-1",
  email: null,
  display_name: null,
  is_anonymous: true,
  is_admin: false,
  home_city: null,
  currency: "USD",
}

export const note: NoteRead = {
  id: "note-1",
  title: "Pack a headlamp",
  content: "Power cuts happen. **Bring one.**",
  color: "yellow",
  is_pinned: true,
  trip_id: TRIP_ID,
  created_at: "2026-11-05T09:00:00Z",
  updated_at: "2026-11-05T09:00:00Z",
}

export const conversation: ConversationRead = {
  id: "conv-1",
  title: "Packing for Kathmandu",
  trip_id: TRIP_ID,
  is_archived: false,
  is_favorite: true,
  last_message_at: "2026-11-05T09:30:00Z",
  created_at: "2026-11-05T09:00:00Z",
}

export const page = <T>(items: T[]) => ({ items, total: items.length, limit: 20, offset: 0 })
