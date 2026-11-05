import { Box, Button, Heading, HStack, Stack, Text } from "@chakra-ui/react"
import { useState } from "react"
import { LuPlus } from "react-icons/lu"
import { formatDay } from "@/lib/format"
import { dayColor } from "@/theme/dayColors"
import type { DayGroup } from "./grouping"
import { useItineraryMutations } from "./hooks"
import { ItemForm } from "./ItemForm"
import { ItemRow } from "./ItemRow"

export function DaySection({
  group,
  theme,
  tripId,
  currency,
  days,
  activeItemId,
  onShowOnMap,
}: {
  group: DayGroup
  theme?: string
  tripId: string
  currency: string
  days: string[]
  activeItemId: string | null
  onShowOnMap: (itemId: string) => void
}) {
  const [adding, setAdding] = useState(false)
  const { add } = useItineraryMutations(tripId)
  const color = dayColor(group.dayIndex)
  const headingId = `day-${group.dayIndex}`

  return (
    <Box as="section" aria-labelledby={headingId}>
      <HStack gap="3" mb="2" align="center">
        <Box
          display="grid"
          placeItems="center"
          w="8"
          h="8"
          borderRadius="full"
          fontFamily="mono"
          fontWeight="700"
          fontSize="sm"
          flexShrink={0}
          style={{ background: color.color, color: color.text }}
          aria-hidden="true"
        >
          {group.dayIndex}
        </Box>
        <Stack gap="0" flex="1" minW="0">
          <Heading as="h3" id={headingId} size="md" fontFamily="heading" fontWeight="600">
            Day {group.dayIndex} · {formatDay(group.day)}
          </Heading>
          {theme && (
            <Text fontSize="sm" color="fg.muted">
              {theme}
            </Text>
          )}
        </Stack>
      </HStack>
      {group.items.length > 0 ? (
        <Stack
          as="ol"
          gap="0"
          ms="4"
          ps="3"
          borderLeftWidth="2px"
          style={{ borderColor: color.color }}
        >
          {group.items.map((item) => (
            <ItemRow
              key={item.id}
              item={item}
              tripId={tripId}
              currency={currency}
              days={days}
              active={item.id === activeItemId}
              onShowOnMap={onShowOnMap}
            />
          ))}
        </Stack>
      ) : (
        <Text fontSize="sm" color="fg.muted" ms="11">
          Nothing planned yet.
        </Text>
      )}
      <Box ms="11" mt="2">
        {adding ? (
          <ItemForm
            days={days}
            defaultDay={group.day}
            submitLabel="Add"
            onCancel={() => setAdding(false)}
            onSubmit={async (body) => {
              await add.mutateAsync({ path: { trip_id: tripId }, body })
              setAdding(false)
            }}
          />
        ) : (
          <Button size="sm" variant="ghost" onClick={() => setAdding(true)}>
            <LuPlus /> Add to day {group.dayIndex}
          </Button>
        )}
      </Box>
    </Box>
  )
}
