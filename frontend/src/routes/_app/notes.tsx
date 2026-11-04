import { createFileRoute } from "@tanstack/react-router"
import { NotesPage } from "@/features/notes/NotesPage"

export const Route = createFileRoute("/_app/notes")({
  component: NotesPage,
})
