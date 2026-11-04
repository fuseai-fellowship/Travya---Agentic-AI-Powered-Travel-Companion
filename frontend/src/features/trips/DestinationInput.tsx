import { Combobox, createListCollection, HStack, Portal, Spinner, Text } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { useMemo } from "react"
import { LuMapPin } from "react-icons/lu"
import { exploreSuggestPlacesOptions } from "@/client/@tanstack/react-query.gen"
import type { PlaceSuggestion } from "@/client/types.gen"
import { useDebouncedValue } from "@/lib/hooks"

/** Free text with OpenStreetMap suggestions from `GET /explore/places`. */
export function DestinationInput({
  value,
  onChange,
  onBlur,
  invalid,
}: {
  value: string
  onChange: (value: string) => void
  onBlur?: () => void
  invalid?: boolean
}) {
  const term = useDebouncedValue(value.trim(), 250)
  const query = useQuery({
    ...exploreSuggestPlacesOptions({ query: { q: term, limit: 6 } }),
    enabled: term.length >= 2,
    staleTime: 5 * 60_000,
  })

  const collection = useMemo(
    () =>
      createListCollection<PlaceSuggestion>({
        items: query.data ?? [],
        itemToString: (place) => place.name,
        itemToValue: (place) => `${place.name}|${place.lat},${place.lon}`,
      }),
    [query.data],
  )

  return (
    <Combobox.Root
      collection={collection}
      inputValue={value}
      onInputValueChange={(details) => onChange(details.inputValue)}
      allowCustomValue
      openOnClick={false}
      selectionBehavior="replace"
      invalid={invalid}
      size="lg"
      positioning={{ sameWidth: true }}
    >
      <Combobox.Label>Destination</Combobox.Label>
      <Combobox.Control>
        <Combobox.Input placeholder="Where to? e.g. Kathmandu" onBlur={onBlur} autoComplete="off" />
        <Combobox.IndicatorGroup>
          {query.isFetching && <Spinner size="xs" color="fg.muted" />}
        </Combobox.IndicatorGroup>
      </Combobox.Control>
      <Portal>
        <Combobox.Positioner>
          <Combobox.Content>
            <Combobox.Empty>
              {term.length < 2 ? "Type at least 2 letters" : "No matching places"}
            </Combobox.Empty>
            {collection.items.map((place) => (
              <Combobox.Item key={collection.getItemValue(place)} item={place}>
                <HStack gap="2" minW="0">
                  <LuMapPin aria-hidden="true" />
                  <Combobox.ItemText>
                    <Text as="span" fontWeight="500">
                      {place.name}
                    </Text>
                    <Text as="span" color="fg.muted" fontSize="xs" ms="2" truncate>
                      {place.display_name}
                    </Text>
                  </Combobox.ItemText>
                </HStack>
              </Combobox.Item>
            ))}
          </Combobox.Content>
        </Combobox.Positioner>
      </Portal>
    </Combobox.Root>
  )
}
