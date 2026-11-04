import { Button, Field, HStack, NumberInput, SegmentGroup, Wrap } from "@chakra-ui/react"
import type { ReactNode } from "react"
import { INTERESTS, PACES } from "./tripSchema"

export const CURRENCIES = [
  "USD",
  "EUR",
  "GBP",
  "JPY",
  "NPR",
  "INR",
  "AUD",
  "CAD",
  "CHF",
  "SGD",
  "THB",
  "CNY",
]

export function TravelersField({
  value,
  onChange,
  error,
}: {
  value: number
  onChange: (value: number) => void
  error?: string
}) {
  return (
    <Field.Root invalid={!!error}>
      <NumberInput.Root
        min={1}
        max={20}
        value={Number.isFinite(value) ? String(value) : ""}
        onValueChange={(details) => onChange(details.valueAsNumber)}
        size="lg"
        maxW="160px"
      >
        <NumberInput.Label>Travelers</NumberInput.Label>
        <NumberInput.Control />
        <NumberInput.Input />
      </NumberInput.Root>
      <Field.ErrorText>{error}</Field.ErrorText>
    </Field.Root>
  )
}

const PACE_LABELS: Record<(typeof PACES)[number], string> = {
  relaxed: "Relaxed",
  balanced: "Balanced",
  packed: "Packed",
}

export function PaceField({
  value,
  onChange,
}: {
  value: (typeof PACES)[number]
  onChange: (value: (typeof PACES)[number]) => void
}) {
  return (
    <Field.Root>
      <Field.Label id="pace-label">Pace</Field.Label>
      <SegmentGroup.Root
        value={value}
        onValueChange={(details) => {
          if (details.value) onChange(details.value as (typeof PACES)[number])
        }}
        aria-labelledby="pace-label"
        size="lg"
      >
        <SegmentGroup.Indicator />
        <SegmentGroup.Items
          items={PACES.map((pace) => ({ value: pace, label: PACE_LABELS[pace] }))}
        />
      </SegmentGroup.Root>
    </Field.Root>
  )
}

export function InterestsField({
  value,
  onChange,
  error,
}: {
  value: string[]
  onChange: (value: string[]) => void
  error?: string
}) {
  const toggle = (interest: string) =>
    onChange(
      value.includes(interest) ? value.filter((item) => item !== interest) : [...value, interest],
    )
  return (
    <Field.Root invalid={!!error}>
      <Field.Label as="span" id="interests-label">
        Interests
      </Field.Label>
      <Wrap gap="2" role="group" aria-labelledby="interests-label">
        {INTERESTS.map((interest) => {
          const on = value.includes(interest)
          return (
            <Button
              key={interest}
              type="button"
              size="sm"
              minH="36px"
              borderRadius="full"
              variant={on ? "solid" : "outline"}
              colorPalette={on ? "sea" : "gray"}
              aria-pressed={on}
              onClick={() => toggle(interest)}
              textTransform="capitalize"
            >
              {interest}
            </Button>
          )
        })}
      </Wrap>
      <Field.ErrorText>{error}</Field.ErrorText>
    </Field.Root>
  )
}

export function FieldRow({ children }: { children: ReactNode }) {
  return (
    <HStack gap="4" align="start" flexWrap={{ base: "wrap", md: "nowrap" }}>
      {children}
    </HStack>
  )
}
