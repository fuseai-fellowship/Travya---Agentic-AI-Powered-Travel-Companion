import {
  Button,
  Container,
  Field,
  Heading,
  HStack,
  Input,
  NativeSelect,
  Stack,
  Text,
  Textarea,
} from "@chakra-ui/react"
import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { getRouteApi, useNavigate } from "@tanstack/react-router"
import { useState } from "react"
import { Controller, type Path, useForm } from "react-hook-form"
import { tripsCreateTripMutation } from "@/client/@tanstack/react-query.gen"
import type { PlaceSuggestion } from "@/client/types.gen"
import { startPlan } from "@/features/planner/planStore"
import { useProfileDefaults } from "@/features/trips/useProfileDefaults"
import { ApiError } from "@/lib/errors"
import { addDays } from "@/lib/format"
import { useDocumentTitle } from "@/lib/hooks"
import { invalidateOperations } from "@/lib/queryKeys"
import { DestinationInput } from "./DestinationInput"
import { emptyFormValues, SAMPLE_TRIPS, sampleFormValues } from "./samples"
import { CURRENCIES, FieldRow, InterestsField, PaceField, TravelersField } from "./TripFormFields"
import { MAX_TRIP_DAYS, type TripFormValues, toTripCreate, tripFormSchema } from "./tripSchema"

const route = getRouteApi("/_app/trips/new")

export function NewTripPage() {
  useDocumentTitle("New trip")
  const { sample: sampleId } = route.useSearch()
  const sample = SAMPLE_TRIPS.find((item) => item.id === sampleId)
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const create = useMutation({
    ...tripsCreateTripMutation(),
    meta: { errorTitle: "Couldn't create the trip" },
  })

  const form = useForm<TripFormValues>({
    resolver: zodResolver(tripFormSchema),
    defaultValues: sample ? sampleFormValues(sample) : emptyFormValues(),
  })
  useProfileDefaults(form, !sample)
  const { register, control, handleSubmit, watch, setError, formState } = form
  const [place, setPlace] = useState<PlaceSuggestion | null>(null)
  const { errors } = formState
  const start = watch("start_date")
  const currency = watch("currency")

  const submit = (plan: boolean) =>
    handleSubmit(async (values) => {
      try {
        const body = toTripCreate(values)
        // Coordinates only while the destination is still the picked suggestion's name.
        const chosen = place?.name === body.destination ? place : null
        const trip = await create.mutateAsync({
          body: chosen
            ? {
                ...body,
                latitude: chosen.lat,
                longitude: chosen.lon,
                country_code: chosen.country_code,
              }
            : body,
        })
        void invalidateOperations(queryClient, "tripsListTrips")
        if (plan) startPlan(queryClient, trip.id)
        await navigate({ to: "/trips/$tripId", params: { tripId: trip.id } })
      } catch (error) {
        if (error instanceof ApiError) {
          for (const field of error.fieldErrors) {
            const name = field.field as Path<TripFormValues>
            if (name in values) setError(name, { message: field.message })
          }
        }
      }
    })

  return (
    <Container maxW="3xl" py={{ base: "6", md: "10" }} px={{ base: "4", md: "8" }}>
      <Stack gap="8">
        <Stack gap="1">
          <Heading as="h1" fontFamily="heading" size="3xl" fontWeight="600">
            {sample ? `Plan ${sample.destination}` : "Plan a new trip"}
          </Heading>
          <Text color="fg.muted">
            Tell the agents the basics. They research in parallel, draft the days and review them.
          </Text>
        </Stack>

        <Stack asChild gap="6">
          <form noValidate onSubmit={submit(true)}>
            <Controller
              control={control}
              name="destination"
              render={({ field, fieldState }) => (
                <Field.Root invalid={!!fieldState.error}>
                  <DestinationInput
                    value={field.value}
                    onChange={field.onChange}
                    onSelect={setPlace}
                    onBlur={field.onBlur}
                    invalid={!!fieldState.error}
                  />
                  <Field.ErrorText>{fieldState.error?.message}</Field.ErrorText>
                </Field.Root>
              )}
            />

            <Field.Root invalid={!!errors.title}>
              <Field.Label>Trip name (optional)</Field.Label>
              <Input placeholder="Defaults to “Trip to …”" {...register("title")} />
              <Field.ErrorText>{errors.title?.message}</Field.ErrorText>
            </Field.Root>

            <FieldRow>
              <Field.Root invalid={!!errors.start_date}>
                <Field.Label>Start date</Field.Label>
                <Input type="date" size="lg" {...register("start_date")} />
                <Field.ErrorText>{errors.start_date?.message}</Field.ErrorText>
              </Field.Root>
              <Field.Root invalid={!!errors.end_date}>
                <Field.Label>End date</Field.Label>
                <Input
                  type="date"
                  size="lg"
                  min={start}
                  max={start ? addDays(start, MAX_TRIP_DAYS - 1) : undefined}
                  {...register("end_date")}
                />
                <Field.HelperText>Up to {MAX_TRIP_DAYS} days</Field.HelperText>
                <Field.ErrorText>{errors.end_date?.message}</Field.ErrorText>
              </Field.Root>
            </FieldRow>

            <FieldRow>
              <Controller
                control={control}
                name="travelers"
                render={({ field, fieldState }) => (
                  <TravelersField
                    value={field.value}
                    onChange={field.onChange}
                    error={fieldState.error?.message}
                  />
                )}
              />
              <Field.Root invalid={!!errors.budget}>
                <Field.Label>Budget (optional)</Field.Label>
                <Input
                  inputMode="decimal"
                  size="lg"
                  placeholder="e.g. 1500"
                  {...register("budget")}
                />
                <Field.ErrorText>{errors.budget?.message}</Field.ErrorText>
              </Field.Root>
              <Field.Root invalid={!!errors.currency} maxW={{ md: "140px" }}>
                <Field.Label>Currency</Field.Label>
                <NativeSelect.Root size="lg">
                  <NativeSelect.Field {...register("currency")}>
                    {(CURRENCIES.includes(currency) ? CURRENCIES : [currency, ...CURRENCIES]).map(
                      (code) => (
                        <option key={code} value={code}>
                          {code}
                        </option>
                      ),
                    )}
                  </NativeSelect.Field>
                  <NativeSelect.Indicator />
                </NativeSelect.Root>
                <Field.ErrorText>{errors.currency?.message}</Field.ErrorText>
              </Field.Root>
            </FieldRow>

            <Controller
              control={control}
              name="pace"
              render={({ field }) => <PaceField value={field.value} onChange={field.onChange} />}
            />
            <Controller
              control={control}
              name="interests"
              render={({ field, fieldState }) => (
                <InterestsField
                  value={field.value}
                  onChange={field.onChange}
                  error={fieldState.error?.message}
                />
              )}
            />

            <Field.Root invalid={!!errors.origin}>
              <Field.Label>Travelling from (optional)</Field.Label>
              <Input placeholder="e.g. London" {...register("origin")} />
              <Field.HelperText>Adds sample flight quotes to the plan.</Field.HelperText>
              <Field.ErrorText>{errors.origin?.message}</Field.ErrorText>
            </Field.Root>

            <Field.Root invalid={!!errors.notes}>
              <Field.Label>Anything else the agents should know?</Field.Label>
              <Textarea
                rows={3}
                placeholder="Dietary needs, mobility, must-sees…"
                {...register("notes")}
              />
              <Field.ErrorText>{errors.notes?.message}</Field.ErrorText>
            </Field.Root>

            <HStack gap="3" flexWrap="wrap">
              <Button
                type="submit"
                size="lg"
                colorPalette="brand"
                loading={formState.isSubmitting}
                loadingText="Creating trip…"
              >
                Plan my trip
              </Button>
              <Button
                type="button"
                size="lg"
                variant="ghost"
                disabled={formState.isSubmitting}
                onClick={submit(false)}
              >
                Save as draft
              </Button>
            </HStack>
          </form>
        </Stack>
      </Stack>
    </Container>
  )
}
