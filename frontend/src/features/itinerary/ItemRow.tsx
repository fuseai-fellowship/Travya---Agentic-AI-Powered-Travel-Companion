import { Badge, Box, HStack, Icon, IconButton, Stack, Text } from "@chakra-ui/react"
import { useEffect, useRef, useState } from "react"
import { LuMapPin, LuPencil, LuTrash2 } from "react-icons/lu"
import type { ItineraryItemRead } from "@/client/types.gen"
import { ConfirmDialog } from "@/components/ConfirmDialog"
import { formatMoney, formatTime, toNumber } from "@/lib/format"
import { CATEGORY_ICONS, CATEGORY_LABELS } from "./categories"
import { useItineraryMutations } from "./hooks"
import { ItemForm } from "./ItemForm"

export function ItemRow({
  item,
  tripId,
  currency,
  days,
  active,
  onShowOnMap,
}: {
  item: ItineraryItemRead
  tripId: string
  currency: string
  days: string[]
  active: boolean
  onShowOnMap: (itemId: string) => void
}) {
  const [editing, setEditing] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const { update, remove } = useItineraryMutations(tripId)
  const ref = useRef<HTMLDivElement>(null)
  const category = item.category ?? "other"
  const cost = toNumber(item.estimated_cost)
  const hasPin = item.latitude !== null && item.latitude !== undefined

  useEffect(() => {
    if (active) ref.current?.scrollIntoView({ block: "nearest", behavior: "smooth" })
  }, [active])

  if (editing) {
    return (
      <Box as="li" listStyleType="none">
        <ItemForm
          days={days}
          item={item}
          defaultDay={item.day}
          submitLabel="Save"
          onCancel={() => setEditing(false)}
          onSubmit={async (body) => {
            await update.mutateAsync({ path: { trip_id: tripId, item_id: item.id }, body })
            setEditing(false)
          }}
        />
      </Box>
    )
  }

  return (
    <HStack
      as="li"
      ref={ref}
      align="start"
      gap="3"
      p="3"
      borderRadius="card"
      bg={active ? "brand.subtle" : "transparent"}
      transition="background 200ms ease-out"
      listStyleType="none"
    >
      <Text
        fontFamily="mono"
        fontSize="sm"
        color="fg.muted"
        minW="44px"
        pt="0.5"
        style={{ fontVariantNumeric: "tabular-nums" }}
      >
        {formatTime(item.start_time) ?? "—"}
      </Text>
      <Icon as={CATEGORY_ICONS[category]} color="fg.muted" mt="1" aria-hidden="true" />
      <Text srOnly>{CATEGORY_LABELS[category]}:</Text>
      <Stack gap="0.5" flex="1" minW="0">
        <HStack gap="2" flexWrap="wrap">
          <Text fontWeight="600">{item.title}</Text>
          <Badge
            size="sm"
            variant="outline"
            colorPalette={item.source === "agent" ? "sea" : "brand"}
          >
            {item.source === "agent" ? "Agent" : "You"}
          </Badge>
        </HStack>
        {item.place_name && item.place_name !== item.title && (
          <Text fontSize="sm" color="fg.muted">
            {item.place_name}
          </Text>
        )}
        {item.description && <Text fontSize="sm">{item.description}</Text>}
        {cost !== null && cost > 0 && (
          <Text
            fontSize="sm"
            fontFamily="mono"
            color="fg.muted"
            style={{ fontVariantNumeric: "tabular-nums" }}
          >
            ≈ {formatMoney(cost, currency)}
          </Text>
        )}
      </Stack>
      <HStack gap="0">
        {hasPin && (
          <IconButton
            variant="ghost"
            size="sm"
            aria-label={`Show ${item.title} on the map`}
            aria-pressed={active}
            onClick={() => onShowOnMap(item.id)}
          >
            <LuMapPin />
          </IconButton>
        )}
        <IconButton
          variant="ghost"
          size="sm"
          aria-label={`Edit ${item.title}`}
          onClick={() => setEditing(true)}
        >
          <LuPencil />
        </IconButton>
        <IconButton
          variant="ghost"
          size="sm"
          aria-label={`Delete ${item.title}`}
          onClick={() => setConfirming(true)}
        >
          <LuTrash2 />
        </IconButton>
      </HStack>
      <ConfirmDialog
        open={confirming}
        onOpenChange={setConfirming}
        title="Delete this item?"
        description={`“${item.title}” will be removed from the itinerary and the map.`}
        confirmLabel="Delete"
        destructive
        loading={remove.isPending}
        onConfirm={() =>
          remove.mutate(
            { path: { trip_id: tripId, item_id: item.id } },
            { onSettled: () => setConfirming(false) },
          )
        }
      />
    </HStack>
  )
}
