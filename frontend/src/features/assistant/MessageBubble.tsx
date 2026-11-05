import { Badge, Box, HStack, IconButton, Stack, Text } from "@chakra-ui/react"
import { useMutation } from "@tanstack/react-query"
import { useState } from "react"
import { LuThumbsDown, LuThumbsUp } from "react-icons/lu"
import { feedbackGiveFeedbackMutation } from "@/client/@tanstack/react-query.gen"
import { Markdown } from "@/components/Markdown"

const TOOL_LABELS: Record<string, string> = {
  search_places: "Searched OpenStreetMap",
  weather_forecast: "Checked the weather",
  destination_guide: "Read the travel guide",
  my_trips: "Looked at your trips",
  trip_itinerary: "Opened your itinerary",
}

export function ToolChips({ tools }: { tools: string[] }) {
  if (!tools.length) return null
  return (
    <HStack gap="1.5" flexWrap="wrap">
      {[...new Set(tools)].map((tool) => (
        <Badge key={tool} size="sm" variant="subtle" colorPalette="sea" borderRadius="full">
          {TOOL_LABELS[tool] ?? tool}
        </Badge>
      ))}
    </HStack>
  )
}

export function MessageBubble({
  id,
  author,
  content,
  tools = [],
  interrupted = false,
}: {
  id?: string
  author: "user" | "assistant"
  content: string
  tools?: string[]
  /** The reply was cut short (stopped, timed out or failed); the API kept what had arrived. */
  interrupted?: boolean
}) {
  const mine = author === "user"
  return (
    <Stack as="li" gap="1.5" align={mine ? "flex-end" : "flex-start"} listStyleType="none">
      <Text srOnly>{mine ? "You said:" : "Travya said:"}</Text>
      {!mine && <ToolChips tools={tools} />}
      <Box
        maxW={{ base: "92%", md: "80%" }}
        px="4"
        py="2.5"
        borderRadius="card"
        bg={mine ? "brand.solid" : "bg.panel"}
        color={mine ? "brand.contrast" : "fg"}
        borderWidth={mine ? "0" : "1px"}
      >
        {mine ? <Text whiteSpace="pre-wrap">{content}</Text> : <Markdown>{content}</Markdown>}
      </Box>
      {!mine && interrupted && (
        <Text fontSize="xs" color="fg.muted" ps="1">
          Interrupted before it finished
        </Text>
      )}
      {!mine && id && <Feedback messageId={id} />}
    </Stack>
  )
}

function Feedback({ messageId }: { messageId: string }) {
  const [rating, setRating] = useState<number | null>(null)
  const feedback = useMutation({
    ...feedbackGiveFeedbackMutation(),
    meta: { errorTitle: "Couldn't send feedback" },
  })
  const rate = (value: number) =>
    feedback.mutate(
      { body: { target_type: "message", target_id: messageId, rating: value } },
      { onSuccess: () => setRating(value) },
    )
  return (
    <HStack gap="0">
      <IconButton
        size="xs"
        variant="ghost"
        aria-label="Helpful answer"
        aria-pressed={rating === 5}
        disabled={feedback.isPending}
        onClick={() => rate(5)}
        color={rating === 5 ? "sea.fg" : "fg.muted"}
      >
        <LuThumbsUp />
      </IconButton>
      <IconButton
        size="xs"
        variant="ghost"
        aria-label="Unhelpful answer"
        aria-pressed={rating === 1}
        disabled={feedback.isPending}
        onClick={() => rate(1)}
        color={rating === 1 ? "brand.fg" : "fg.muted"}
      >
        <LuThumbsDown />
      </IconButton>
    </HStack>
  )
}
