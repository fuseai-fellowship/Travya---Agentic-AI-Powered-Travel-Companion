import { HStack, Icon, Stack, Text } from "@chakra-ui/react"
import { formatTemp, weatherIcon } from "@/features/weather/weatherIcon"
import { formatDay } from "@/lib/format"
import type { PreviewWeather } from "./timeline"

/** Compact day chips from the weather scout's preview. */
export function WeatherStrip({ days }: { days: PreviewWeather[] }) {
  if (!days.length) return null
  return (
    <HStack
      as="ul"
      gap="2"
      overflowX="auto"
      pb="1"
      aria-label="Weather outlook"
      listStyleType="none"
    >
      {days.map((day) => (
        <Stack
          as="li"
          key={day.day}
          gap="0.5"
          align="center"
          minW="72px"
          px="2"
          py="1.5"
          borderWidth="1px"
          borderRadius="card"
          bg="bg.panel"
          title={day.summary}
        >
          <Text fontSize="xs" color="fg.muted">
            {formatDay(day.day, { month: undefined })}
          </Text>
          <Icon as={weatherIcon(day.weather_code)} boxSize="5" color="sea.fg" aria-hidden="true" />
          <Text srOnly>{day.summary}</Text>
          <Text fontFamily="mono" fontSize="xs" style={{ fontVariantNumeric: "tabular-nums" }}>
            {formatTemp(day.temp_min_c)} / {formatTemp(day.temp_max_c)}
          </Text>
        </Stack>
      ))}
    </HStack>
  )
}
