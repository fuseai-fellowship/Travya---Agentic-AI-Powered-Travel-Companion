import {
  Box,
  Button,
  CloseButton,
  chakra,
  Dialog,
  Field,
  HStack,
  Input,
  NativeSelect,
  Portal,
  Stack,
  Switch,
  Tabs,
  Textarea,
} from "@chakra-ui/react"
import { zodResolver } from "@hookform/resolvers/zod"
import { useId } from "react"
import { Controller, useForm } from "react-hook-form"
import { z } from "zod"
import type { NoteCreate, NoteRead } from "@/client/types.gen"
import { Markdown } from "@/components/Markdown"
import { NOTE_COLORS, NOTE_TONES, noteColor } from "./colors"

const schema = z.object({
  title: z.string().trim().min(1, "Give the note a title").max(200),
  content: z.string().max(10_000, "Use at most 10,000 characters"),
  color: z.enum(NOTE_COLORS),
  is_pinned: z.boolean(),
  trip_id: z.string(),
})
type Values = z.infer<typeof schema>

const Swatch = chakra("button")

export function NoteEditor({
  open,
  note,
  trips,
  fixedTripId,
  saving,
  onClose,
  onSave,
  onDelete,
}: {
  open: boolean
  note: NoteRead | null
  trips: Array<{ id: string; title: string }>
  fixedTripId?: string
  saving: boolean
  onClose: () => void
  onSave: (body: NoteCreate) => void
  onDelete?: (note: NoteRead) => void
}) {
  const { register, control, handleSubmit, watch, formState } = useForm<Values>({
    resolver: zodResolver(schema),
    values: {
      title: note?.title ?? "",
      content: note?.content ?? "",
      color: noteColor(note?.color ?? "yellow"),
      is_pinned: note?.is_pinned ?? false,
      trip_id: fixedTripId ?? note?.trip_id ?? "",
    },
  })
  const content = watch("content")
  const formId = useId()

  const submit = handleSubmit((values) =>
    onSave({
      title: values.title,
      content: values.content,
      color: values.color,
      is_pinned: values.is_pinned,
      trip_id: values.trip_id || null,
    }),
  )

  return (
    <Dialog.Root
      open={open}
      onOpenChange={(details) => !details.open && onClose()}
      size={{ base: "full", md: "lg" }}
    >
      <Portal>
        <Dialog.Backdrop />
        <Dialog.Positioner>
          <Dialog.Content>
            <Dialog.Header>
              <Dialog.Title fontFamily="heading">{note ? "Edit note" : "New note"}</Dialog.Title>
            </Dialog.Header>
            <Dialog.Body>
              <Stack asChild gap="4">
                <form id={formId} onSubmit={submit} noValidate>
                  <Field.Root invalid={!!formState.errors.title}>
                    <Field.Label>Title</Field.Label>
                    <Input {...register("title")} />
                    <Field.ErrorText>{formState.errors.title?.message}</Field.ErrorText>
                  </Field.Root>
                  <Tabs.Root defaultValue="write" size="sm" variant="line">
                    <Tabs.List>
                      <Tabs.Trigger value="write">Write</Tabs.Trigger>
                      <Tabs.Trigger value="preview">Preview</Tabs.Trigger>
                    </Tabs.List>
                    <Tabs.Content value="write">
                      <Field.Root invalid={!!formState.errors.content}>
                        <Field.Label srOnly>Note (Markdown)</Field.Label>
                        <Textarea
                          rows={8}
                          placeholder="Markdown works: **bold**, lists, links"
                          {...register("content")}
                        />
                        <Field.ErrorText>{formState.errors.content?.message}</Field.ErrorText>
                      </Field.Root>
                    </Tabs.Content>
                    <Tabs.Content value="preview">
                      <Box minH="180px" p="3" borderWidth="1px" borderRadius="md">
                        <Markdown>{content || "_Nothing to preview yet._"}</Markdown>
                      </Box>
                    </Tabs.Content>
                  </Tabs.Root>
                  <Controller
                    control={control}
                    name="color"
                    render={({ field }) => (
                      <Field.Root>
                        <Field.Label as="span" id="note-color">
                          Colour
                        </Field.Label>
                        <HStack role="radiogroup" aria-labelledby="note-color" gap="2">
                          {NOTE_COLORS.map((color) => (
                            <Swatch
                              type="button"
                              key={color}
                              role="radio"
                              aria-checked={field.value === color}
                              aria-label={color}
                              onClick={() => field.onChange(color)}
                              w="9"
                              h="9"
                              borderRadius="full"
                              borderWidth="2px"
                              borderColor={field.value === color ? "fg" : "border"}
                              style={{ background: NOTE_TONES[color].light }}
                            />
                          ))}
                        </HStack>
                      </Field.Root>
                    )}
                  />
                  <HStack gap="6" flexWrap="wrap" align="end">
                    <Controller
                      control={control}
                      name="is_pinned"
                      render={({ field }) => (
                        <Switch.Root
                          checked={field.value}
                          onCheckedChange={(details) => field.onChange(details.checked)}
                        >
                          <Switch.HiddenInput />
                          <Switch.Control />
                          <Switch.Label>Pin to top</Switch.Label>
                        </Switch.Root>
                      )}
                    />
                    {!fixedTripId && (
                      <Field.Root flex="1" minW="200px">
                        <Field.Label>Trip</Field.Label>
                        <NativeSelect.Root size="sm">
                          <NativeSelect.Field {...register("trip_id")}>
                            <option value="">No trip</option>
                            {trips.map((trip) => (
                              <option key={trip.id} value={trip.id}>
                                {trip.title}
                              </option>
                            ))}
                          </NativeSelect.Field>
                          <NativeSelect.Indicator />
                        </NativeSelect.Root>
                      </Field.Root>
                    )}
                  </HStack>
                </form>
              </Stack>
            </Dialog.Body>
            <Dialog.Footer justifyContent="space-between">
              {note && onDelete ? (
                <Button variant="ghost" colorPalette="red" onClick={() => onDelete(note)}>
                  Delete
                </Button>
              ) : (
                <span />
              )}
              <HStack>
                <Button variant="outline" onClick={onClose}>
                  Cancel
                </Button>
                <Button type="submit" form={formId} colorPalette="brand" loading={saving}>
                  Save note
                </Button>
              </HStack>
            </Dialog.Footer>
            <Dialog.CloseTrigger asChild>
              <CloseButton size="sm" aria-label="Close" />
            </Dialog.CloseTrigger>
          </Dialog.Content>
        </Dialog.Positioner>
      </Portal>
    </Dialog.Root>
  )
}
