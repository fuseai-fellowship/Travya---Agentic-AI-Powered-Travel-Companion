import { Box, Heading, HStack, IconButton, Stack, Text } from "@chakra-ui/react"
import { LuPin, LuPinOff } from "react-icons/lu"
import type { NoteRead } from "@/client/types.gen"
import { Markdown } from "@/components/Markdown"
import { formatRelative } from "@/lib/format"
import { NOTE_TONES, noteColor } from "./colors"

export function NoteCard({
  note,
  tripName,
  onOpen,
  onTogglePin,
}: {
  note: NoteRead
  tripName?: string
  onOpen: (note: NoteRead) => void
  onTogglePin: (note: NoteRead) => void
}) {
  const tone = NOTE_TONES[noteColor(note.color)]
  return (
    <Stack
      as="li"
      gap="2"
      p="4"
      minH="160px"
      borderRadius="card"
      borderTopWidth="4px"
      listStyleType="none"
      boxShadow="card"
      style={{ borderTopColor: tone.edge }}
      bg={{ base: tone.light, _dark: tone.dark }}
      color="fg"
      position="relative"
    >
      <HStack justify="space-between" align="start" gap="2">
        <Heading as="h3" size="md" fontFamily="heading" fontWeight="600" lineClamp={2}>
          <Box
            as="button"
            textAlign="left"
            onClick={() => onOpen(note)}
            _focusVisible={{
              outline: "2px solid",
              outlineColor: "brand.focusRing",
              outlineOffset: "2px",
            }}
            _after={{ content: '""', position: "absolute", inset: "0", borderRadius: "card" }}
          >
            {note.title}
          </Box>
        </Heading>
        <IconButton
          size="sm"
          variant="ghost"
          position="relative"
          zIndex="1"
          aria-label={note.is_pinned ? `Unpin ${note.title}` : `Pin ${note.title}`}
          aria-pressed={note.is_pinned}
          onClick={() => onTogglePin(note)}
        >
          {note.is_pinned ? <LuPin /> : <LuPinOff />}
        </IconButton>
      </HStack>
      {note.content && (
        <Box
          flex="1"
          overflow="hidden"
          maxH="160px"
          css={{ maskImage: "linear-gradient(to bottom, black 75%, transparent)" }}
        >
          <Markdown>{note.content}</Markdown>
        </Box>
      )}
      <HStack justify="space-between" fontSize="xs" color="fg.muted" mt="auto">
        <Text>{formatRelative(note.updated_at)}</Text>
        {tripName && (
          <Text truncate maxW="60%">
            {tripName}
          </Text>
        )}
      </HStack>
    </Stack>
  )
}
