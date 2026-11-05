import { Button, HStack, SimpleGrid, Stack, Text } from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useMemo, useState } from "react"
import { LuPlus, LuStickyNote } from "react-icons/lu"
import {
  notesCreateNoteMutation,
  notesDeleteNoteMutation,
  notesListNotesOptions,
  notesUpdateNoteMutation,
  tripsListTripsOptions,
} from "@/client/@tanstack/react-query.gen"
import type { NoteCreate, NoteRead } from "@/client/types.gen"
import { ConfirmDialog } from "@/components/ConfirmDialog"
import { Empty, ErrorState, ListSkeleton } from "@/components/States"
import { notifySuccess } from "@/lib/notify"
import { invalidateOperations } from "@/lib/queryKeys"
import { NoteCard } from "./NoteCard"
import { NoteEditor } from "./NoteEditor"

/** The sticky-note board, for all notes or one trip's notes. */
export function NoteBoard({ tripId }: { tripId?: string }) {
  const queryClient = useQueryClient()
  const [editing, setEditing] = useState<NoteRead | "new" | null>(null)
  const [deleting, setDeleting] = useState<NoteRead | null>(null)
  const notes = useQuery(notesListNotesOptions({ query: { trip_id: tripId, limit: 100 } }))
  const trips = useQuery({ ...tripsListTripsOptions({ query: { limit: 100 } }), enabled: !tripId })
  const refresh = () => invalidateOperations(queryClient, "notesListNotes")

  const create = useMutation({
    ...notesCreateNoteMutation(),
    meta: { errorTitle: "Couldn't save the note" },
    onSuccess: refresh,
  })
  const update = useMutation({
    ...notesUpdateNoteMutation(),
    meta: { errorTitle: "Couldn't save the note" },
    onSuccess: refresh,
  })
  const remove = useMutation({
    ...notesDeleteNoteMutation(),
    meta: { errorTitle: "Couldn't delete the note" },
    onSuccess: () => {
      notifySuccess("Note deleted")
      return refresh()
    },
  })

  const tripNames = useMemo(
    () => new Map((trips.data?.items ?? []).map((trip) => [trip.id, trip.destination])),
    [trips.data],
  )
  const sorted = useMemo(
    () =>
      [...(notes.data?.items ?? [])].sort(
        (a, b) =>
          Number(b.is_pinned) - Number(a.is_pinned) || b.updated_at.localeCompare(a.updated_at),
      ),
    [notes.data],
  )

  const save = (body: NoteCreate) => {
    const done = { onSuccess: () => setEditing(null) }
    if (editing && editing !== "new") update.mutate({ path: { note_id: editing.id }, body }, done)
    else create.mutate({ body: { ...body, trip_id: tripId ?? body.trip_id } }, done)
  }

  const togglePin = (note: NoteRead) =>
    update.mutate({ path: { note_id: note.id }, body: { is_pinned: !note.is_pinned } })

  return (
    <Stack gap="4">
      <HStack justify="space-between" gap="3">
        <Text fontSize="sm" color="fg.muted">
          {notes.data ? `${notes.data.total} note${notes.data.total === 1 ? "" : "s"}` : " "}
        </Text>
        <Button colorPalette="brand" size="sm" onClick={() => setEditing("new")}>
          <LuPlus /> New note
        </Button>
      </HStack>
      {notes.isPending ? (
        <ListSkeleton rows={2} height="160px" />
      ) : notes.isError ? (
        <ErrorState
          error={notes.error}
          title="Couldn't load notes"
          onRetry={() => notes.refetch()}
        />
      ) : sorted.length === 0 ? (
        <Empty
          icon={<LuStickyNote />}
          title="No notes yet"
          description="Jot down ideas, addresses and reminders. Markdown works."
        />
      ) : (
        <SimpleGrid
          as="ul"
          columns={{ base: 1, sm: 2, xl: tripId ? 2 : 3 }}
          gap="4"
          aria-label="Notes"
        >
          {sorted.map((note) => (
            <NoteCard
              key={note.id}
              note={note}
              tripName={tripId ? undefined : note.trip_id ? tripNames.get(note.trip_id) : undefined}
              onOpen={setEditing}
              onTogglePin={togglePin}
            />
          ))}
        </SimpleGrid>
      )}
      <NoteEditor
        open={editing !== null}
        note={editing === "new" ? null : editing}
        trips={(trips.data?.items ?? []).map((trip) => ({
          id: trip.id,
          title: `${trip.destination} · ${trip.title}`,
        }))}
        fixedTripId={tripId}
        saving={create.isPending || update.isPending}
        onClose={() => setEditing(null)}
        onSave={save}
        onDelete={(note) => {
          setEditing(null)
          setDeleting(note)
        }}
      />
      <ConfirmDialog
        open={deleting !== null}
        onOpenChange={(open) => !open && setDeleting(null)}
        title="Delete this note?"
        description={`“${deleting?.title ?? ""}” will be deleted.`}
        confirmLabel="Delete"
        destructive
        loading={remove.isPending}
        onConfirm={() =>
          deleting &&
          remove.mutate({ path: { note_id: deleting.id } }, { onSettled: () => setDeleting(null) })
        }
      />
    </Stack>
  )
}
