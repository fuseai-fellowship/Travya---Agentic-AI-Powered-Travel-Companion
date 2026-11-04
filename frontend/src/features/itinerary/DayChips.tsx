import { Box, Button, HStack } from "@chakra-ui/react"
import { formatDay } from "@/lib/format"
import { dayColor } from "@/theme/dayColors"
import type { DayGroup } from "./grouping"

/** Day filter shared by the list and the map. */
export function DayChips({
  days,
  selected,
  onSelect,
}: {
  days: DayGroup[]
  selected: number | null
  onSelect: (dayIndex: number | null) => void
}) {
  return (
    <HStack role="group" aria-label="Show day" gap="2" overflowX="auto" pb="1" flexWrap="nowrap">
      <Button
        size="sm"
        borderRadius="full"
        minH="36px"
        variant={selected === null ? "solid" : "outline"}
        aria-pressed={selected === null}
        onClick={() => onSelect(null)}
      >
        All days
      </Button>
      {days.map((day) => {
        const on = selected === day.dayIndex
        return (
          <Button
            key={day.day}
            size="sm"
            borderRadius="full"
            minH="36px"
            variant={on ? "solid" : "outline"}
            aria-pressed={on}
            title={formatDay(day.day)}
            onClick={() => onSelect(on ? null : day.dayIndex)}
          >
            <Box
              as="span"
              w="2.5"
              h="2.5"
              borderRadius="full"
              bg={dayColor(day.dayIndex).color}
              borderWidth="1px"
              borderColor="white"
              aria-hidden="true"
            />
            Day {day.dayIndex}
          </Button>
        )
      })}
    </HStack>
  )
}
