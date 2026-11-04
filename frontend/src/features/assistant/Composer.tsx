import { Box, Button, HStack, Text, Textarea } from "@chakra-ui/react"
import { type KeyboardEvent, useId, useState } from "react"
import { LuSend, LuSquare } from "react-icons/lu"

const MAX = 4000

export function Composer({
  disabled,
  streaming,
  onSend,
  onStop,
}: {
  disabled?: boolean
  streaming: boolean
  onSend: (content: string) => void
  onStop: () => void
}) {
  const [text, setText] = useState("")
  const id = useId()
  const trimmed = text.trim()

  const submit = () => {
    if (!trimmed || streaming || disabled) return
    onSend(trimmed)
    setText("")
  }

  const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    // Enter sends, Shift+Enter adds a line; never send mid-composition (IME).
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault()
      submit()
    }
  }

  return (
    <Box
      as="form"
      onSubmit={(event) => {
        event.preventDefault()
        submit()
      }}
      borderWidth="1px"
      borderRadius="card"
      bg="bg.panel"
      p="2"
      _focusWithin={{ borderColor: "brand.focusRing" }}
    >
      <label htmlFor={id}>
        <Text srOnly>Message the travel assistant</Text>
      </label>
      <Textarea
        id={id}
        value={text}
        onChange={(event) => setText(event.target.value.slice(0, MAX))}
        onKeyDown={onKeyDown}
        placeholder="Ask about places, weather, food or your itinerary…"
        rows={2}
        resize="none"
        border="0"
        _focusVisible={{ outline: "none", boxShadow: "none" }}
        autoresize
        maxH="40vh"
        disabled={disabled}
      />
      <HStack justify="space-between" px="2">
        <Text fontSize="xs" color="fg.muted">
          {text.length > MAX * 0.8
            ? `${text.length}/${MAX}`
            : "Enter to send · Shift+Enter for a new line"}
        </Text>
        {streaming ? (
          <Button size="sm" variant="outline" onClick={onStop}>
            <LuSquare /> Stop
          </Button>
        ) : (
          <Button type="submit" size="sm" colorPalette="brand" disabled={!trimmed || disabled}>
            <LuSend /> Send
          </Button>
        )}
      </HStack>
    </Box>
  )
}
