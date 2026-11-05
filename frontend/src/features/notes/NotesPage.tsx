import { Container, Heading, Stack, Text } from "@chakra-ui/react"
import { useDocumentTitle } from "@/lib/hooks"
import { NoteBoard } from "./NoteBoard"

export function NotesPage() {
  useDocumentTitle("Notes")
  return (
    <Container maxW="6xl" py={{ base: "6", md: "10" }} px={{ base: "4", md: "8" }}>
      <Stack gap="6">
        <Stack gap="1">
          <Heading as="h1" fontFamily="heading" size="3xl" fontWeight="600">
            Notes
          </Heading>
          <Text color="fg.muted">A sticky-note board for ideas, addresses and reminders.</Text>
        </Stack>
        <NoteBoard />
      </Stack>
    </Container>
  )
}
