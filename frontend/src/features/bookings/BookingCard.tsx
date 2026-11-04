import { Badge, Button, HStack, Stack, Text } from "@chakra-ui/react"
import type { BookingRead } from "@/client/types.gen"
import { formatMoney, toNumber } from "@/lib/format"

const STATUS_PALETTE = { quoted: "gray", confirmed: "green", cancelled: "red" } as const

function humanize(key: string): string {
  const text = key.replace(/_/g, " ")
  return text.charAt(0).toUpperCase() + text.slice(1)
}

/** A few readable facts from the free-form `details` object (scalar values only). */
export function bookingFacts(details: Record<string, unknown>, limit = 4): Array<[string, string]> {
  return Object.entries(details)
    .filter(([, value]) => ["string", "number", "boolean"].includes(typeof value))
    .slice(0, limit)
    .map(([key, value]) => [
      humanize(key),
      typeof value === "boolean" ? (value ? "Yes" : "No") : String(value),
    ])
}

export function BookingCard({
  booking,
  onConfirm,
  onCancel,
}: {
  booking: BookingRead
  onConfirm: (booking: BookingRead) => void
  onCancel: (booking: BookingRead) => void
}) {
  const amount = toNumber(booking.amount)
  const facts = bookingFacts(booking.details)
  return (
    <Stack
      as="li"
      gap="2"
      p="4"
      borderWidth="1px"
      borderRadius="card"
      bg="bg.panel"
      listStyleType="none"
    >
      <HStack justify="space-between" align="start" gap="3">
        <Stack gap="0" minW="0">
          <Text fontWeight="600">{booking.title}</Text>
          <Text fontSize="sm" color="fg.muted">
            {booking.provider}
          </Text>
        </Stack>
        <Stack gap="1" align="end" flexShrink={0}>
          <Text fontFamily="mono" fontWeight="600" style={{ fontVariantNumeric: "tabular-nums" }}>
            {amount === null ? booking.amount : formatMoney(amount, booking.currency)}
          </Text>
          <Badge colorPalette={STATUS_PALETTE[booking.status]} size="sm" borderRadius="full">
            {booking.status === "quoted"
              ? "Quote"
              : booking.status === "confirmed"
                ? "Booked"
                : "Cancelled"}
          </Badge>
        </Stack>
      </HStack>
      {facts.length > 0 && (
        <HStack as="dl" gap="4" flexWrap="wrap" fontSize="sm" rowGap="1">
          {facts.map(([label, value]) => (
            <HStack key={label} gap="1">
              <Text as="dt" color="fg.muted">
                {label}
              </Text>
              <Text as="dd">{value}</Text>
            </HStack>
          ))}
        </HStack>
      )}
      <HStack justify="space-between" gap="3" flexWrap="wrap">
        {booking.status === "confirmed" && booking.confirmation_code ? (
          <Text fontSize="sm">
            Code{" "}
            <Text as="span" fontFamily="mono" fontWeight="600" letterSpacing="wider">
              {booking.confirmation_code}
            </Text>
            {booking.is_simulated && (
              <Text as="span" color="fg.muted">
                {" "}
                (simulated)
              </Text>
            )}
          </Text>
        ) : (
          <span />
        )}
        {booking.status === "quoted" && (
          <Button size="sm" colorPalette="brand" onClick={() => onConfirm(booking)}>
            Confirm booking
          </Button>
        )}
        {booking.status === "confirmed" && (
          <Button size="sm" variant="outline" onClick={() => onCancel(booking)}>
            Cancel booking
          </Button>
        )}
      </HStack>
    </Stack>
  )
}
