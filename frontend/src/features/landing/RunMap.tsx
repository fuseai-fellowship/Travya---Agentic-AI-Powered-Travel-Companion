import { Box, type BoxProps, Image, Text } from "@chakra-ui/react"
import { dayColor } from "@/theme/dayColors"
import type { ProjectedMap } from "./runs"

/**
 * A recorded run on a static basemap: the real OpenFreeMap tiles for that trip rendered once, with
 * the places, stops and routes drawn on top in the same pixel space. No MapLibre on the landing
 * page. Image and overlay both fill the box with "cover" cropping, so they stay aligned.
 *
 * The motion signature lives here: pins drop and routes draw, with the `map` easing and duration.
 */
export function RunMap({
  map,
  light,
  dark,
  label,
  showPlaces = false,
  showStops = true,
  animate = true,
  priority = false,
  ...box
}: {
  map: ProjectedMap
  light: string
  dark: string
  /** Accessible description of the map image. */
  label: string
  showPlaces?: boolean
  showStops?: boolean
  animate?: boolean
  /** Load the basemap eagerly (hero) instead of lazily. */
  priority?: boolean
} & BoxProps) {
  const { width, height } = map
  const pin = (delay: number) =>
    animate
      ? {
          animationName: "pin-drop",
          animationDuration: "map",
          animationTimingFunction: "map",
          animationFillMode: "both",
          animationDelay: `${delay}ms`,
        }
      : undefined

  return (
    <Box position="relative" overflow="hidden" bg="bg.muted" {...box}>
      <Image
        src={light}
        alt=""
        width={width}
        height={height}
        loading={priority ? "eager" : "lazy"}
        decoding="async"
        position="absolute"
        inset="0"
        w="full"
        h="full"
        objectFit="cover"
        _dark={{ display: "none" }}
      />
      <Image
        src={dark}
        alt=""
        width={width}
        height={height}
        loading="lazy"
        decoding="async"
        position="absolute"
        inset="0"
        w="full"
        h="full"
        objectFit="cover"
        display="none"
        _dark={{ display: "block" }}
      />
      <Box
        asChild
        position="absolute"
        inset="0"
        w="full"
        h="full"
        css={{
          "& .pin": { transformBox: "fill-box", transformOrigin: "center bottom" },
          "& .route": { strokeDasharray: 1 },
        }}
      >
        <svg
          viewBox={`0 0 ${width} ${height}`}
          preserveAspectRatio="xMidYMid slice"
          role="img"
          aria-label={label}
        >
          {showPlaces &&
            !showStops &&
            map.places?.map(([x, y], index) => (
              <Box
                asChild
                key={`${x}-${y}-${index.toString()}`}
                className="pin"
                css={pin(Math.min(index * 18, 700))}
              >
                <circle
                  cx={x}
                  cy={y}
                  r="5"
                  fill="var(--chakra-colors-pin-solid)"
                  fillOpacity="0.75"
                  stroke="var(--chakra-colors-bg-panel)"
                  strokeWidth="1.5"
                />
              </Box>
            ))}
          {showStops && (
            <>
              {map.routes.map((route) => (
                <Box
                  asChild
                  key={`route-${route.day}`}
                  className="route"
                  css={
                    animate
                      ? {
                          animationName: "route-draw",
                          animationDuration: "map",
                          animationTimingFunction: "map",
                          animationFillMode: "both",
                          animationDelay: `${(route.day - 1) * 160}ms`,
                        }
                      : undefined
                  }
                >
                  <polyline
                    points={route.points.map((point) => point.join(",")).join(" ")}
                    pathLength={1}
                    fill="none"
                    stroke={dayColor(route.day).color}
                    strokeWidth="5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    opacity="0.9"
                  />
                </Box>
              ))}
              {map.stops.map((stop, index) => {
                const color = dayColor(stop.day)
                const order = map.stops.slice(0, index).filter((s) => s.day === stop.day).length + 1
                return (
                  <Box
                    asChild
                    key={`${stop.day}-${order}`}
                    className="pin"
                    css={pin((stop.day - 1) * 160 + order * 60)}
                  >
                    <g>
                      <title>{`Day ${stop.day}, stop ${order}: ${stop.place ?? stop.title}`}</title>
                      <circle
                        cx={stop.x}
                        cy={stop.y}
                        r="13"
                        fill={color.color}
                        stroke="#FFFFFF"
                        strokeWidth="2.5"
                      />
                      <text
                        x={stop.x}
                        y={stop.y + 4}
                        textAnchor="middle"
                        fontSize="11"
                        fontWeight="700"
                        fill={color.text}
                        fontFamily="'Overpass Mono Variable', ui-monospace, monospace"
                      >
                        {stop.day}·{order}
                      </text>
                    </g>
                  </Box>
                )
              })}
            </>
          )}
        </svg>
      </Box>
      <Text
        position="absolute"
        right="0"
        bottom="0"
        px="1.5"
        py="0.5"
        fontSize="2xs"
        color="fg.muted"
        bg="bg.panel/85"
        borderTopLeftRadius="sm"
      >
        ©{" "}
        <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">
          OpenStreetMap
        </a>{" "}
        contributors · OpenFreeMap
      </Text>
    </Box>
  )
}
