import type { TripMap } from "@/client/types.gen"
import { dayColor } from "@/theme/dayColors"

export interface Stop {
  itemId: string
  title: string
  placeName: string | null
  category: string
  day: string
  dayIndex: number
  /** 1-based order within its day. */
  order: number
  startTime: string | null
  lon: number
  lat: number
  color: string
  textColor: string
}

export interface RouteLine {
  day: string
  dayIndex: number
  color: string
  coordinates: [number, number][]
  distanceM: number | null
  durationS: number | null
}

export type Bounds = [[number, number], [number, number]]

function num(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null
}

function str(value: unknown): string | null {
  return typeof value === "string" ? value : null
}

/** Splits the backend FeatureCollection into numbered stops and per-day route lines. */
export function parseTripMap(map: TripMap | undefined): { stops: Stop[]; routes: RouteLine[] } {
  if (!map) return { stops: [], routes: [] }
  const stops: Stop[] = []
  const routes: RouteLine[] = []
  const perDay = new Map<number, number>()

  for (const feature of map.features) {
    const props = feature.properties
    const geometry = feature.geometry as { type?: string; coordinates?: unknown }
    const dayIndex = num(props.day_index) ?? 1
    const { color, text } = dayColor(dayIndex)

    if (props.kind === "stop" && geometry.type === "Point" && Array.isArray(geometry.coordinates)) {
      const [lon, lat] = geometry.coordinates as unknown[]
      const lonValue = num(lon)
      const latValue = num(lat)
      if (lonValue === null || latValue === null) continue
      const order = (perDay.get(dayIndex) ?? 0) + 1
      perDay.set(dayIndex, order)
      stops.push({
        itemId: str(props.item_id) ?? `${dayIndex}-${order}`,
        title: str(props.title) ?? "Stop",
        placeName: str(props.place_name),
        category: str(props.category) ?? "other",
        day: str(props.day) ?? "",
        dayIndex,
        order,
        startTime: str(props.start_time),
        lon: lonValue,
        lat: latValue,
        color,
        textColor: text,
      })
    }

    if (
      props.kind === "route" &&
      geometry.type === "LineString" &&
      Array.isArray(geometry.coordinates)
    ) {
      const coordinates = (geometry.coordinates as unknown[]).flatMap((point) => {
        if (!Array.isArray(point)) return []
        const lonValue = num(point[0])
        const latValue = num(point[1])
        return lonValue === null || latValue === null
          ? []
          : [[lonValue, latValue] as [number, number]]
      })
      if (coordinates.length < 2) continue
      routes.push({
        day: str(props.day) ?? "",
        dayIndex,
        color,
        coordinates,
        distanceM: num(props.distance_m),
        durationS: num(props.duration_s),
      })
    }
  }
  return { stops, routes }
}

/** [[west, south], [east, north]] around the given points, or null when there are none. */
export function boundsOf(points: Array<{ lon: number; lat: number }>): Bounds | null {
  if (!points.length) return null
  let west = Infinity
  let south = Infinity
  let east = -Infinity
  let north = -Infinity
  for (const { lon, lat } of points) {
    west = Math.min(west, lon)
    east = Math.max(east, lon)
    south = Math.min(south, lat)
    north = Math.max(north, lat)
  }
  return [
    [west, south],
    [east, north],
  ]
}

export function routesGeoJson(routes: RouteLine[], selectedDay: number | null) {
  return {
    type: "FeatureCollection" as const,
    features: routes.map((route) => ({
      type: "Feature" as const,
      geometry: { type: "LineString" as const, coordinates: route.coordinates },
      properties: {
        color: route.color,
        dim: selectedDay !== null && route.dayIndex !== selectedDay,
      },
    })),
  }
}

export function placesGeoJson(places: Array<{ name: string; lon: number; lat: number }>) {
  return {
    type: "FeatureCollection" as const,
    features: places.map((place) => ({
      type: "Feature" as const,
      geometry: { type: "Point" as const, coordinates: [place.lon, place.lat] },
      properties: { name: place.name },
    })),
  }
}
