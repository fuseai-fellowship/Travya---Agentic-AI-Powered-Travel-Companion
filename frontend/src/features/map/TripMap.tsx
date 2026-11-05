import "maplibre-gl/dist/maplibre-gl.css"
import { Box, chakra, Text, VisuallyHidden } from "@chakra-ui/react"
import { setWorkerUrl } from "maplibre-gl"
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?url"
import { useEffect, useMemo, useRef } from "react"
import { LuMapPin } from "react-icons/lu"
import MapGL, {
  AttributionControl,
  Layer,
  type MapRef,
  Marker,
  NavigationControl,
  Popup,
  Source,
} from "react-map-gl/maplibre"
import { useColorMode } from "@/components/ui/color-mode"
import { formatTime } from "@/lib/format"
import { usePrefersReducedMotion } from "@/lib/hooks"
import {
  type Bounds,
  boundsOf,
  placesGeoJson,
  type RouteLine,
  routesGeoJson,
  type Stop,
} from "./mapData"

// MapLibre 6 resolves its worker next to its own module, which a bundler moves; point at the asset.
setWorkerUrl(workerUrl)

export const MAP_STYLES = {
  light: "https://tiles.openfreemap.org/styles/positron",
  dark: "https://tiles.openfreemap.org/styles/dark",
} as const

export interface TripMapProps {
  center: [number, number] | null
  stops: Stop[]
  routes: RouteLine[]
  places: Array<{ name: string; lon: number; lat: number }>
  selectedDay: number | null
  activeItemId: string | null
  onSelectItem: (itemId: string | null) => void
}

const StopButton = chakra("button")

export default function TripMap({
  center,
  stops,
  routes,
  places,
  selectedDay,
  activeItemId,
  onSelectItem,
}: TripMapProps) {
  const mapRef = useRef<MapRef>(null)
  const reducedMotion = usePrefersReducedMotion()
  const { colorMode } = useColorMode()
  const visibleStops =
    selectedDay === null ? stops : stops.filter((stop) => stop.dayIndex === selectedDay)
  const active = stops.find((stop) => stop.itemId === activeItemId) ?? null

  const bounds: Bounds | null = useMemo(() => {
    if (visibleStops.length) return boundsOf(visibleStops)
    if (places.length) return boundsOf(places)
    return null
  }, [visibleStops, places])
  const boundsKey = bounds
    ? bounds
        .flat()
        .map((value) => value.toFixed(4))
        .join(",")
    : ""

  // biome-ignore lint/correctness/useExhaustiveDependencies: refit only when the bounds change
  useEffect(() => {
    const map = mapRef.current
    if (!map || !bounds) return
    const [[west, south], [east, north]] = bounds
    if (west === east && south === north) {
      map.flyTo({ center: [west, south], zoom: 14, duration: reducedMotion ? 0 : 600 })
    } else {
      map.fitBounds(bounds, { padding: 56, maxZoom: 15, duration: reducedMotion ? 0 : 700 })
    }
  }, [boundsKey, reducedMotion])

  return (
    <MapGL
      ref={mapRef}
      initialViewState={
        center
          ? { longitude: center[0], latitude: center[1], zoom: 11 }
          : { longitude: 10, latitude: 25, zoom: 1.4 }
      }
      mapStyle={MAP_STYLES[colorMode === "dark" ? "dark" : "light"]}
      attributionControl={false}
      style={{ width: "100%", height: "100%" }}
      onClick={() => onSelectItem(null)}
      cooperativeGestures={false}
    >
      <NavigationControl position="top-right" showCompass={false} />
      <AttributionControl
        compact={false}
        position="bottom-right"
        customAttribution='<a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">© OpenStreetMap contributors</a>'
      />

      {places.length > 0 && (
        <Source id="research-places" type="geojson" data={placesGeoJson(places)}>
          <Layer
            id="research-places"
            type="circle"
            paint={{
              "circle-radius": 4,
              "circle-color": "#0E7C7B",
              "circle-opacity": stops.length ? 0.25 : 0.7,
              "circle-stroke-color": "#FFFFFF",
              "circle-stroke-width": 1,
              "circle-opacity-transition": { duration: reducedMotion ? 0 : 400 },
            }}
          />
        </Source>
      )}

      {routes.length > 0 && (
        <Source id="routes" type="geojson" data={routesGeoJson(routes, selectedDay)}>
          <Layer
            id="routes"
            type="line"
            layout={{ "line-join": "round", "line-cap": "round" }}
            paint={{
              "line-color": ["get", "color"],
              "line-width": 4,
              "line-opacity": ["case", ["get", "dim"], 0.2, 0.9],
            }}
          />
        </Source>
      )}

      {center && stops.length === 0 && (
        <Marker longitude={center[0]} latitude={center[1]} anchor="bottom">
          <Box color="brand.solid" fontSize="32px" aria-hidden="true">
            <LuMapPin />
          </Box>
        </Marker>
      )}

      {stops.map((stop) => {
        const dimmed = selectedDay !== null && stop.dayIndex !== selectedDay
        const isActive = stop.itemId === activeItemId
        return (
          <Marker key={stop.itemId} longitude={stop.lon} latitude={stop.lat} anchor="center">
            <StopButton
              type="button"
              aria-pressed={isActive}
              onClick={(event) => {
                event.stopPropagation()
                onSelectItem(stop.itemId)
              }}
              display="grid"
              placeItems="center"
              minW="30px"
              h="30px"
              px="1.5"
              borderRadius="full"
              borderWidth="2px"
              borderColor="white"
              boxShadow={isActive ? "0 0 0 3px #1C1B19" : "0 1px 3px rgba(0,0,0,0.35)"}
              fontFamily="mono"
              fontSize="11px"
              fontWeight="700"
              cursor="pointer"
              opacity={dimmed ? 0.35 : 1}
              transform={isActive ? "scale(1.15)" : "none"}
              transition="transform 150ms ease-out, opacity 200ms ease-out"
              style={{ background: stop.color, color: stop.textColor }}
            >
              <span aria-hidden="true">
                {stop.dayIndex}·{stop.order}
              </span>
              <VisuallyHidden>
                Day {stop.dayIndex}, stop {stop.order}: {stop.title}
              </VisuallyHidden>
            </StopButton>
          </Marker>
        )
      })}

      {active && (
        <Popup
          longitude={active.lon}
          latitude={active.lat}
          anchor="bottom"
          offset={20}
          closeOnClick={false}
          onClose={() => onSelectItem(null)}
          maxWidth="260px"
        >
          <Box color="#1C1B19" p="1">
            <Text fontSize="xs" color="#6B665E">
              Day {active.dayIndex}
              {active.startTime ? ` · ${formatTime(active.startTime)}` : ""}
            </Text>
            <Text fontWeight="600" fontSize="sm">
              {active.title}
            </Text>
            {active.placeName && active.placeName !== active.title && (
              <Text fontSize="xs">{active.placeName}</Text>
            )}
          </Box>
        </Popup>
      )}
    </MapGL>
  )
}
