import { Box, Button, Grid, Stack } from "@chakra-ui/react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { getRouteApi } from "@tanstack/react-router"
import { useMemo, useState } from "react"
import { LuMaximize2, LuMinimize2 } from "react-icons/lu"
import {
  tripsGetTripOptions,
  tripsListBookingsOptions,
  tripsTripMapOptions,
} from "@/client/@tanstack/react-query.gen"
import { NotFound } from "@/components/RouteFallbacks"
import { ErrorState, ListSkeleton } from "@/components/States"
import { readPlan } from "@/features/itinerary/plan"
import { MapPanel } from "@/features/map/MapPanel"
import { parseTripMap } from "@/features/map/mapData"
import { PlanningPanel } from "@/features/planner/PlanningPanel"
import { retryPlan, startPlan, stopPlan, usePlanRun } from "@/features/planner/planStore"
import { ApiError } from "@/lib/errors"
import { useDocumentTitle } from "@/lib/hooks"
import { computeBudget } from "./budget"
import { TripHeader } from "./TripHeader"
import { TripTabs } from "./TripTabs"

const route = getRouteApi("/_app/trips/$tripId")

export function TripPage() {
  const { tripId } = route.useParams()
  const queryClient = useQueryClient()
  const run = usePlanRun(tripId)
  const planning = run?.active ?? false
  const [selectedDay, setSelectedDay] = useState<number | null>(null)
  const [activeItemId, setActiveItemId] = useState<string | null>(null)
  const [mapExpanded, setMapExpanded] = useState(false)

  const trip = useQuery({
    ...tripsGetTripOptions({ path: { trip_id: tripId } }),
    // Planning started in another tab: poll until it finishes.
    refetchInterval: (query) =>
      query.state.data?.status === "planning" && !planning ? 4000 : false,
  })
  const bookings = useQuery(tripsListBookingsOptions({ path: { trip_id: tripId } }))
  const hasPlan = Boolean(trip.data?.plan)
  const map = useQuery({
    ...tripsTripMapOptions({ path: { trip_id: tripId } }),
    enabled: hasPlan && !planning,
  })
  useDocumentTitle(trip.data?.destination)

  const plan = useMemo(() => readPlan(trip.data?.plan), [trip.data?.plan])
  const { stops, routes } = useMemo(() => parseTripMap(map.data), [map.data])
  const budget = computeBudget({
    budget: trip.data?.budget,
    currency: trip.data?.currency ?? "USD",
    estimatedTotal: plan?.estimatedTotal ?? null,
    bookings: bookings.data ?? [],
  })

  if (trip.isPending) {
    return (
      <Box p={{ base: "4", md: "8" }} maxW="3xl">
        <ListSkeleton rows={4} height="96px" />
      </Box>
    )
  }
  if (trip.isError) {
    if (trip.error instanceof ApiError && (trip.error.status === 404 || trip.error.status === 422))
      return <NotFound />
    return (
      <Box p={{ base: "4", md: "8" }} maxW="3xl">
        <ErrorState
          error={trip.error}
          title="Couldn't load this trip"
          onRetry={() => trip.refetch()}
        />
      </Box>
    )
  }

  const data = trip.data
  const center: [number, number] | null =
    data.longitude !== null && data.latitude !== null
      ? [data.longitude, data.latitude]
      : (map.data?.center ?? null)
  const replan = (instructions?: string) => startPlan(queryClient, tripId, instructions)

  return (
    <Grid
      templateColumns={{
        base: "minmax(0, 1fr)",
        lg: "minmax(0, 600px) minmax(0, 1fr)",
        "2xl": "minmax(0, 680px) minmax(0, 1fr)",
      }}
      templateAreas={{ base: `"header" "map" "panel"`, lg: `"header map" "panel map"` }}
      templateRows={{ lg: "auto 1fr" }}
      minH={{ lg: "100dvh" }}
    >
      <Box gridArea="header" px={{ base: "4", md: "8" }} pt={{ base: "4", md: "6" }} pb="4">
        <TripHeader trip={data} budget={budget} planning={planning} onReplan={replan} />
      </Box>
      <Box
        gridArea="map"
        position={{ base: "relative", lg: "sticky" }}
        top="0"
        h={{ base: mapExpanded ? "75dvh" : "40dvh", lg: "100dvh" }}
        transition="height 250ms ease-out"
        borderLeftWidth={{ lg: "1px" }}
      >
        <MapPanel
          center={center}
          stops={stops}
          routes={routes}
          places={stops.length ? [] : (run?.state.places ?? [])}
          selectedDay={selectedDay}
          activeItemId={activeItemId}
          onSelectItem={setActiveItemId}
        />
        <Button
          display={{ base: "inline-flex", lg: "none" }}
          position="absolute"
          left="2"
          top="2"
          size="sm"
          variant="surface"
          aria-expanded={mapExpanded}
          onClick={() => setMapExpanded((value) => !value)}
        >
          {mapExpanded ? <LuMinimize2 /> : <LuMaximize2 />}
          {mapExpanded ? "Smaller map" : "Bigger map"}
        </Button>
      </Box>
      <Stack
        gridArea="panel"
        gap="5"
        px={{ base: "4", md: "8" }}
        pb="10"
        pt={{ base: "4", lg: "0" }}
      >
        <PlanningPanel
          tripId={tripId}
          run={run}
          planningElsewhere={data.status === "planning"}
          onRetry={() => retryPlan(queryClient, tripId)}
          onStop={() => stopPlan(tripId)}
        />
        <TripTabs
          trip={data}
          planning={planning}
          selectedDay={selectedDay}
          onSelectDay={(day) => {
            setSelectedDay(day)
            setActiveItemId(null)
          }}
          activeItemId={activeItemId}
          onSelectItem={setActiveItemId}
          onPlan={() => replan()}
        />
      </Stack>
    </Grid>
  )
}
