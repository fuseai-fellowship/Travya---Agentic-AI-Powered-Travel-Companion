import { Badge, HStack, Icon, SimpleGrid, Stack, Text } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { LuCloudSun, LuDroplets } from "react-icons/lu"
import { tripsTripWeatherOptions } from "@/client/@tanstack/react-query.gen"
import { Empty, ErrorState, ListSkeleton } from "@/components/States"
import { formatDay } from "@/lib/format"
import { formatTemp, weatherIcon } from "./weatherIcon"

export function WeatherTab({ tripId, hasLocation }: { tripId: string; hasLocation: boolean }) {
  const query = useQuery({
    ...tripsTripWeatherOptions({ path: { trip_id: tripId } }),
    enabled: hasLocation,
  })

  if (!hasLocation) {
    return (
      <Empty
        icon={<LuCloudSun />}
        title="No forecast yet"
        description="Weather appears once the destination has been located."
      />
    )
  }
  if (query.isPending) return <ListSkeleton rows={3} />
  if (query.isError)
    return (
      <ErrorState
        error={query.error}
        title="Couldn't load the weather"
        onRetry={() => query.refetch()}
      />
    )
  if (!query.data.length) return <Empty icon={<LuCloudSun />} title="No forecast available" />

  const estimate = query.data.some((day) => day.is_climate_estimate)

  return (
    <Stack gap="3">
      {estimate && (
        <Text fontSize="sm" color="fg.muted">
          Days marked <strong>estimate</strong> are too far ahead for a forecast. They show one
          recent year's observed weather for those dates (or a climate-model run) from Open-Meteo,
          not a forecast or a long-term average.
        </Text>
      )}
      <SimpleGrid as="ul" columns={{ base: 1, sm: 2 }} gap="2" listStyleType="none">
        {query.data.map((day) => (
          <HStack
            as="li"
            key={day.day}
            gap="3"
            p="3"
            borderWidth="1px"
            borderRadius="card"
            bg="bg.panel"
            align="start"
          >
            <Icon
              as={weatherIcon(day.weather_code)}
              boxSize="7"
              color="sea.fg"
              aria-hidden="true"
            />
            <Stack gap="0.5" flex="1">
              <HStack justify="space-between">
                <Text fontWeight="600">{formatDay(day.day)}</Text>
                <Text fontFamily="mono" style={{ fontVariantNumeric: "tabular-nums" }}>
                  {formatTemp(day.temp_min_c)} / {formatTemp(day.temp_max_c)}
                </Text>
              </HStack>
              <Text fontSize="sm" color="fg.muted">
                {day.summary}
              </Text>
              <HStack gap="3" fontSize="xs" color="fg.muted">
                <HStack gap="1">
                  <LuDroplets aria-hidden="true" />
                  <Text>
                    {day.precipitation_mm.toFixed(1)} mm
                    {day.precipitation_probability !== null
                      ? ` · ${day.precipitation_probability}%`
                      : ""}
                  </Text>
                </HStack>
                {day.is_climate_estimate && (
                  <Badge size="sm" variant="outline">
                    Estimate
                  </Badge>
                )}
              </HStack>
            </Stack>
          </HStack>
        ))}
      </SimpleGrid>
      <Text fontSize="xs" color="fg.muted">
        Weather data by Open-Meteo.com (CC BY 4.0).
      </Text>
    </Stack>
  )
}
