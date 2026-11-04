import { Tabs } from "@chakra-ui/react"
import { getRouteApi } from "@tanstack/react-router"
import type { TripDetail } from "@/client/types.gen"
import { BookingsTab } from "@/features/bookings/BookingsTab"
import { DocumentsTab } from "@/features/documents/DocumentsTab"
import { ItineraryTab } from "@/features/itinerary/ItineraryTab"
import { NoteBoard } from "@/features/notes/NoteBoard"
import { PhotosTab } from "@/features/photos/PhotosTab"
import { WeatherTab } from "@/features/weather/WeatherTab"
import { TAB_LABELS, TRIP_TABS, type TripTab } from "./tabs"

const route = getRouteApi("/_app/trips/$tripId")

export function TripTabs({
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
  const { tab = "itinerary" } = route.useSearch()
  const navigate = route.useNavigate()

  return (
    <Tabs.Root
      value={tab}
      onValueChange={(details) =>
        navigate({
          search: (prev) => ({
            ...prev,
            tab: details.value === "itinerary" ? undefined : (details.value as TripTab),
          }),
          replace: true,
        })
      }
      lazyMount
      variant="line"
      colorPalette="brand"
    >
      <Tabs.List
        overflowX="auto"
        overflowY="hidden"
        flexWrap="nowrap"
        bg="bg"
        position="sticky"
        top={{ base: "56px", lg: "0" }}
        zIndex="1"
      >
        {TRIP_TABS.map((value) => (
          <Tabs.Trigger key={value} value={value} minH="44px" flexShrink={0}>
            {TAB_LABELS[value]}
          </Tabs.Trigger>
        ))}
      </Tabs.List>
      <Tabs.Content value="itinerary" pt="5">
        <ItineraryTab
          trip={trip}
          planning={planning}
          selectedDay={selectedDay}
          onSelectDay={onSelectDay}
          activeItemId={activeItemId}
          onSelectItem={onSelectItem}
          onPlan={onPlan}
        />
      </Tabs.Content>
      <Tabs.Content value="bookings" pt="5">
        <BookingsTab tripId={trip.id} />
      </Tabs.Content>
      <Tabs.Content value="weather" pt="5">
        <WeatherTab
          tripId={trip.id}
          hasLocation={trip.latitude !== null && trip.longitude !== null}
        />
      </Tabs.Content>
      <Tabs.Content value="photos" pt="5">
        <PhotosTab tripId={trip.id} />
      </Tabs.Content>
      <Tabs.Content value="notes" pt="5">
        <NoteBoard tripId={trip.id} />
      </Tabs.Content>
      <Tabs.Content value="documents" pt="5">
        <DocumentsTab tripId={trip.id} />
      </Tabs.Content>
    </Tabs.Root>
  )
}
