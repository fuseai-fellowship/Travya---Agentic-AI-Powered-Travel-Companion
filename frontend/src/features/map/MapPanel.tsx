import { Box, Center, Skeleton, Text } from "@chakra-ui/react"
import { Component, lazy, type ReactNode, Suspense } from "react"
import type { TripMapProps } from "./TripMap"

// MapLibre is ~1 MB: load it only where a map is shown.
const TripMap = lazy(() => import("./TripMap"))

class MapErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false }

  static getDerivedStateFromError() {
    return { failed: true }
  }

  render() {
    if (this.state.failed) {
      return (
        <Center h="full" bg="bg.muted" p="6" textAlign="center">
          <Text color="fg.muted" fontSize="sm">
            The map couldn't load in this browser (WebGL is unavailable). The itinerary list has
            every stop.
          </Text>
        </Center>
      )
    }
    return this.props.children
  }
}

export function MapPanel(props: TripMapProps) {
  return (
    <Box position="relative" h="full" w="full" bg="bg.muted" overflow="hidden">
      <MapErrorBoundary>
        <Suspense fallback={<Skeleton h="full" w="full" borderRadius="0" />}>
          <TripMap {...props} />
        </Suspense>
      </MapErrorBoundary>
    </Box>
  )
}
