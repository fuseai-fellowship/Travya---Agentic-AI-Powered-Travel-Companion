import {
  Button,
  Field,
  HStack,
  Input,
  NativeSelect,
  SimpleGrid,
  Stack,
  Textarea,
} from "@chakra-ui/react"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { z } from "zod"
import type { ItemCategory, ItineraryItemCreate, ItineraryItemRead } from "@/client/types.gen"
import { formatDay, formatTime } from "@/lib/format"
import { CATEGORY_LABELS, ITEM_CATEGORIES } from "./categories"

const schema = z
  .object({
    title: z.string().trim().min(1, "Give the item a title").max(200),
    day: z.string().min(1),
    start_time: z.string(),
    end_time: z.string(),
    category: z.enum(ITEM_CATEGORIES),
    place_name: z.string().trim().max(300),
    estimated_cost: z
      .string()
      .trim()
      .refine(
        (value) => value === "" || /^\d+(\.\d{1,2})?$/.test(value),
        "Enter an amount like 25",
      ),
    description: z.string().max(2000),
  })
  .refine(
    (values) => !values.start_time || !values.end_time || values.end_time >= values.start_time,
    {
      path: ["end_time"],
      message: "Ends before it starts",
    },
  )
type Values = z.infer<typeof schema>

export function toItemBody(values: Values): ItineraryItemCreate {
  return {
    title: values.title.trim(),
    day: values.day,
    start_time: values.start_time || null,
    end_time: values.end_time || null,
    category: values.category as ItemCategory,
    place_name: values.place_name.trim() || null,
    estimated_cost: values.estimated_cost || null,
    description: values.description.trim() || null,
  }
}

export function ItemForm({
  days,
  item,
  defaultDay,
  submitLabel,
  onSubmit,
  onCancel,
}: {
  days: string[]
  item?: ItineraryItemRead
  defaultDay: string
  submitLabel: string
  onSubmit: (body: ItineraryItemCreate) => Promise<unknown>
  onCancel: () => void
}) {
  const { register, handleSubmit, formState } = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: {
      title: item?.title ?? "",
      day: item?.day ?? defaultDay,
      start_time: formatTime(item?.start_time) ?? "",
      end_time: formatTime(item?.end_time) ?? "",
      category: item?.category ?? "sight",
      place_name: item?.place_name ?? "",
      estimated_cost: item?.estimated_cost ?? "",
      description: item?.description ?? "",
    },
  })
  const { errors, isSubmitting } = formState

  return (
    <Stack asChild gap="3" p="3" borderWidth="1px" borderRadius="card" bg="bg.subtle">
      <form
        noValidate
        onSubmit={handleSubmit(async (values) => {
          await onSubmit(toItemBody(values)).catch(() => undefined)
        })}
      >
        <Field.Root invalid={!!errors.title}>
          <Field.Label>Title</Field.Label>
          <Input autoFocus {...register("title")} />
          <Field.ErrorText>{errors.title?.message}</Field.ErrorText>
        </Field.Root>
        <SimpleGrid columns={{ base: 1, sm: 3 }} gap="3">
          <Field.Root>
            <Field.Label>Day</Field.Label>
            <NativeSelect.Root>
              <NativeSelect.Field {...register("day")}>
                {days.map((day, index) => (
                  <option key={day} value={day}>
                    Day {index + 1} · {formatDay(day)}
                  </option>
                ))}
              </NativeSelect.Field>
              <NativeSelect.Indicator />
            </NativeSelect.Root>
          </Field.Root>
          <Field.Root>
            <Field.Label>Starts</Field.Label>
            <Input type="time" {...register("start_time")} />
          </Field.Root>
          <Field.Root invalid={!!errors.end_time}>
            <Field.Label>Ends</Field.Label>
            <Input type="time" {...register("end_time")} />
            <Field.ErrorText>{errors.end_time?.message}</Field.ErrorText>
          </Field.Root>
        </SimpleGrid>
        <SimpleGrid columns={{ base: 1, sm: 3 }} gap="3">
          <Field.Root>
            <Field.Label>Category</Field.Label>
            <NativeSelect.Root>
              <NativeSelect.Field {...register("category")}>
                {ITEM_CATEGORIES.map((category) => (
                  <option key={category} value={category}>
                    {CATEGORY_LABELS[category]}
                  </option>
                ))}
              </NativeSelect.Field>
              <NativeSelect.Indicator />
            </NativeSelect.Root>
          </Field.Root>
          <Field.Root>
            <Field.Label>Place</Field.Label>
            <Input {...register("place_name")} />
          </Field.Root>
          <Field.Root invalid={!!errors.estimated_cost}>
            <Field.Label>Cost</Field.Label>
            <Input inputMode="decimal" {...register("estimated_cost")} />
            <Field.ErrorText>{errors.estimated_cost?.message}</Field.ErrorText>
          </Field.Root>
        </SimpleGrid>
        <Field.Root>
          <Field.Label>Notes</Field.Label>
          <Textarea rows={2} {...register("description")} />
        </Field.Root>
        <HStack justify="flex-end">
          <Button variant="ghost" onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit" colorPalette="brand" loading={isSubmitting}>
            {submitLabel}
          </Button>
        </HStack>
      </form>
    </Stack>
  )
}
