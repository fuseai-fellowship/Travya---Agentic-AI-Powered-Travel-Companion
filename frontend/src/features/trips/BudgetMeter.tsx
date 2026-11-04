import { Box, HStack, Stack, Text } from "@chakra-ui/react"
import { formatMoney } from "@/lib/format"
import type { BudgetSummary } from "./budget"

const mono = { fontVariantNumeric: "tabular-nums" } as const

/** Confirmed bookings (solid) and the plan estimate (marker) against the trip budget. */
export function BudgetMeter({ summary }: { summary: BudgetSummary }) {
  const { currency, budget, planned, confirmed } = summary
  const money = (value: number) => formatMoney(value, currency)

  if (budget === null) {
    return (
      <Text fontSize="sm" color="fg.muted">
        No budget set
        {planned !== null && (
          <>
            {" "}
            · plan estimate{" "}
            <Text as="span" fontFamily="mono" color="fg" style={mono}>
              {money(planned)}
            </Text>
          </>
        )}
        {confirmed > 0 && (
          <>
            {" "}
            · booked{" "}
            <Text as="span" fontFamily="mono" color="fg" style={mono}>
              {money(confirmed)}
            </Text>
          </>
        )}
      </Text>
    )
  }

  const label = [
    `Budget ${money(budget)}`,
    planned !== null ? `plan estimate ${money(planned)}` : "no plan estimate yet",
    `booked ${money(confirmed)}`,
  ].join(", ")

  return (
    <Stack gap="1.5" minW={{ base: "full", md: "280px" }}>
      <Box
        role="meter"
        aria-label="Budget used"
        aria-valuemin={0}
        aria-valuemax={budget}
        aria-valuenow={Math.min(confirmed, budget)}
        aria-valuetext={label}
        position="relative"
        h="2.5"
        borderRadius="full"
        bg="bg.emphasized"
        overflow="visible"
      >
        <Box
          h="full"
          borderRadius="full"
          bg={summary.overBudget ? "red.solid" : "sea.solid"}
          w={`${summary.confirmedPct ?? 0}%`}
          transition="width 250ms ease-out"
        />
        {summary.plannedPct !== null && (
          <Box
            position="absolute"
            top="-1"
            bottom="-1"
            w="2px"
            bg="brand.solid"
            left={`calc(${summary.plannedPct}% - 1px)`}
            title={`Plan estimate ${money(planned ?? 0)}`}
          />
        )}
      </Box>
      <HStack justify="space-between" fontSize="xs" color="fg.muted" gap="3" flexWrap="wrap">
        <Text>
          Booked{" "}
          <Text as="span" fontFamily="mono" color="fg" style={mono}>
            {money(confirmed)}
          </Text>
        </Text>
        {planned !== null && (
          <Text>
            <Box
              as="span"
              display="inline-block"
              w="2"
              h="2"
              bg="brand.solid"
              mr="1"
              aria-hidden="true"
            />
            Plan{" "}
            <Text
              as="span"
              fontFamily="mono"
              color={planned > budget ? "red.fg" : "fg"}
              style={mono}
            >
              {money(planned)}
            </Text>
          </Text>
        )}
        <Text>
          Budget{" "}
          <Text as="span" fontFamily="mono" color="fg" style={mono}>
            {money(budget)}
          </Text>
        </Text>
      </HStack>
      {summary.otherCurrencies.length > 0 && (
        <Text fontSize="xs" color="fg.muted">
          Bookings in {summary.otherCurrencies.join(", ")} aren't converted.
        </Text>
      )}
    </Stack>
  )
}
