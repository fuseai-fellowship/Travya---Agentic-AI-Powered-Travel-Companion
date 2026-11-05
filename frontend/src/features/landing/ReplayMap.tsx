import { Box } from "@chakra-ui/react"
import { dayColor } from "@/theme/dayColors"
import { REPLAY_DAYS, REPLAY_PLACES } from "./replayScript"

const WIDTH = 320
const HEIGHT = 220
const PAD = 22
const lons = REPLAY_PLACES.map((place) => place.lon)
const lats = REPLAY_PLACES.map((place) => place.lat)
const [west, east, south, north] = [
  Math.min(...lons),
  Math.max(...lons),
  Math.min(...lats),
  Math.max(...lats),
]

function project(lon: number, lat: number): [number, number] {
  const x = PAD + ((lon - west) / (east - west)) * (WIDTH - PAD * 2)
  const y = PAD + ((north - lat) / (north - south)) * (HEIGHT - PAD * 2)
  return [Math.round(x), Math.round(y)]
}

/** A lightweight SVG stand-in for the live map in the landing replay (no MapLibre on this page). */
export function ReplayMap({ showPlaces, showStops }: { showPlaces: boolean; showStops: boolean }) {
  return (
    <Box
      borderRadius="card"
      overflow="hidden"
      borderWidth="1px"
      bg={{ base: "#F2EFE9", _dark: "#22211E" }}
    >
      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        width="100%"
        role="img"
        aria-label="Map of the Kathmandu Valley filling with researched places and the planned route"
      >
        <path
          d="M10 150 C 80 120, 120 175, 190 140 S 290 90, 315 120"
          fill="none"
          stroke="currentColor"
          strokeOpacity="0.12"
          strokeWidth="6"
        />
        {REPLAY_PLACES.map((place, index) => {
          const [x, y] = project(place.lon, place.lat)
          return (
            <circle
              key={place.name}
              cx={x}
              cy={y}
              r="3.5"
              fill="#0E7C7B"
              opacity={showPlaces ? (showStops ? 0.25 : 0.8) : 0}
              style={{ transition: `opacity 300ms ease-out ${index * 40}ms` }}
            />
          )
        })}
        {REPLAY_DAYS.map((stops, dayIndex) => {
          const color = dayColor(dayIndex + 1)
          const points = stops.map((stop) => {
            const place = REPLAY_PLACES[stop]
            return place ? project(place.lon, place.lat) : ([0, 0] as [number, number])
          })
          return (
            <g
              key={stops.join("-")}
              opacity={showStops ? 1 : 0}
              style={{ transition: `opacity 300ms ease-out ${dayIndex * 150}ms` }}
            >
              <polyline
                points={points.map((point) => point.join(",")).join(" ")}
                fill="none"
                stroke={color.color}
                strokeWidth="3"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              {points.map(([x, y], order) => (
                <g key={`${x}-${y}`}>
                  <circle
                    cx={x}
                    cy={y}
                    r="8"
                    fill={color.color}
                    stroke="#FFFFFF"
                    strokeWidth="1.5"
                  />
                  <text
                    x={x}
                    y={y + 3}
                    textAnchor="middle"
                    fontSize="8"
                    fontWeight="700"
                    fill={color.text}
                    fontFamily="monospace"
                  >
                    {dayIndex + 1}·{order + 1}
                  </text>
                </g>
              ))}
            </g>
          )
        })}
      </svg>
    </Box>
  )
}
