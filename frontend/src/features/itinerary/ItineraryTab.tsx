import { Button, Stack } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { useMemo } from "react"
import { LuRoute } from "react-icons/lu"
import { tripsListItineraryOptions } from "@/client/@tanstack/react-query.gen"
import type { TripDetail } from "@/client/types.gen"
import { Empty, ErrorState, ListSkeleton } from "@/components/States"
import { DayChips } from "./DayChips"
import { DaySection } from "./DaySection"
import { groupByDay } from "./grouping"
import { PlanDetails } from "./PlanDetails"
import { readPlan } from "./plan"

export function ItineraryTab({
  trip,
  planning,
  selectedDay,
  onSelectDay,
  activeItemId,
  onSelectItem,
  onPlan,
}: {
  trip: TripDetail
  planning: boolean
  selectedDay: number | null
  onSelectDay: (day: number | null) => void
  activeItemId: string | null
  onSelectItem: (itemId: string | null) => void
  onPlan: () => void
}) {
  const query = useQuery(tripsListItineraryOptions({ path: { trip_id: trip.id } }))
  const plan = useMemo(() => readPlan(trip.plan), [trip.plan])
  const groups = useMemo(
    () => groupByDay(query.data ?? [], trip.start_date, trip.end_date),
    [query.data, trip.start_date, trip.end_date],
  )
  const days = groups.map((group) => group.day)
  const currency = trip.currency ?? "USD"

  if (query.isPending) return <ListSkeleton rows={4} />
  if (query.isError)
    return (
      <ErrorState
        error={query.error}
        title="Couldn't load the itinerary"
        onRetry={() => query.refetch()}
      />
    )

  // Just after a plan finishes, the cached empty list is refetching: don't flash "No itinerary".
  if (!query.data.length && query.isFetching) return <ListSkeleton rows={4} />

  if (!query.data.length && !planning) {
    return (
      <Empty
        icon={<LuRoute />}
        title="No itinerary yet"
        description="Let the agents research and draft the days, or add your own items."
      >
        <Button colorPalette="brand" onClick={onPlan}>
          Plan with agents
        </Button>
        {groups[0] && (
          <DaySection
            group={groups[0]}
            tripId={trip.id}
            currency={currency}
            days={days}
            activeItemId={null}
            onShowOnMap={onSelectItem}
          />
        )}
      </Empty>
    )
  }

  const visible =
    selectedDay === null ? groups : groups.filter((group) => group.dayIndex === selectedDay)

  return (
    <Stack gap="6">
      <DayChips days={groups} selected={selectedDay} onSelect={onSelectDay} />
      {visible.map((group) => (
        <DaySection
          key={group.day}
          group={group}
          theme={plan?.themes[group.day]}
          tripId={trip.id}
          currency={currency}
          days={days}
          activeItemId={activeItemId}
          onShowOnMap={(itemId) => {
            onSelectDay(group.dayIndex)
            onSelectItem(itemId)
          }}
        />
      ))}
      {plan && <PlanDetails plan={plan} tripId={trip.id} currency={currency} />}
    </Stack>
  )
}
