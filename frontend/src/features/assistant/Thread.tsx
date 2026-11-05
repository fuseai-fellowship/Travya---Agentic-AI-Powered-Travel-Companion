import { Alert, Box, Button, Heading, Stack, Text, Wrap } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { useEffect, useRef } from "react"
import { LuMessageCircle } from "react-icons/lu"
import { chatListMessagesOptions } from "@/client/@tanstack/react-query.gen"
import { ErrorState, ListSkeleton } from "@/components/States"
import { Composer } from "./Composer"
import { MessageBubble } from "./MessageBubble"
import type { PendingTurn } from "./useChat"

export function suggestedPrompts(destination?: string): string[] {
  const place = destination ?? "Kathmandu"
  return [
    `What should I pack for ${place} next month?`,
    `Find vegetarian-friendly places to eat in ${place}`,
    `What's a good rainy-day plan in ${place}?`,
  ]
}

export function Thread({
  conversationId,
  pending,
  streaming,
  destination,
  onSend,
  onStop,
}: {
  conversationId?: string
  pending: PendingTurn | null
  streaming: boolean
  destination?: string
  onSend: (content: string) => void
  onStop: () => void
}) {
  const messages = useQuery({
    ...chatListMessagesOptions({
      path: { conversation_id: conversationId ?? "" },
      query: { limit: 200 },
    }),
    enabled: Boolean(conversationId),
  })
  const end = useRef<HTMLDivElement>(null)
  const turn =
    pending && (!conversationId || pending.conversationId === conversationId) ? pending : null
  const items = conversationId ? (messages.data?.items ?? []) : []

  // biome-ignore lint/correctness/useExhaustiveDependencies: scroll as the reply streams in
  useEffect(() => {
    end.current?.scrollIntoView({ block: "end" })
  }, [items.length, turn?.reply, turn?.tools.length])

  const empty = !items.length && !turn

  return (
    <Stack h="full" gap="3" minH="0">
      <Box flex="1" overflowY="auto" minH="0" px={{ base: "0", md: "2" }}>
        {conversationId && messages.isPending ? (
          <ListSkeleton rows={3} height="64px" />
        ) : messages.isError ? (
          <ErrorState
            error={messages.error}
            title="Couldn't load messages"
            onRetry={() => messages.refetch()}
          />
        ) : empty ? (
          <Stack align="center" textAlign="center" gap="4" py="10" px="4">
            <Box color="brand.fg" fontSize="3xl" aria-hidden="true">
              <LuMessageCircle />
            </Box>
            <Heading as="h2" fontFamily="heading" size="xl">
              Ask the travel assistant
            </Heading>
            <Text color="fg.muted" maxW="md">
              It can search OpenStreetMap, check the weather, read Wikivoyage and look at your
              trips.
            </Text>
            <Wrap justify="center" gap="2">
              {suggestedPrompts(destination).map((prompt) => (
                <Button
                  key={prompt}
                  size="sm"
                  variant="outline"
                  borderRadius="full"
                  disabled={streaming}
                  onClick={() => onSend(prompt)}
                >
                  {prompt}
                </Button>
              ))}
            </Wrap>
          </Stack>
        ) : (
          <Stack
            as="ol"
            gap="4"
            py="2"
            role="log"
            aria-live="polite"
            aria-relevant="additions text"
            aria-label="Conversation"
          >
            {items.map((message) => (
              <MessageBubble
                key={message.id}
                id={message.id}
                author={message.role}
                content={message.content}
                tools={Array.isArray(message.meta?.tools) ? (message.meta.tools as string[]) : []}
              />
            ))}
            {turn && (
              <>
                <MessageBubble author="user" content={turn.user} />
                {!turn.unsent && (turn.reply || turn.tools.length > 0 || streaming) && (
                  <MessageBubble
                    author="assistant"
                    content={turn.reply}
                    tools={turn.tools}
                    streaming={streaming}
                  />
                )}
              </>
            )}
          </Stack>
        )}
        {turn?.error && (
          <Alert.Root status="error" mt="3" borderRadius="card">
            <Alert.Indicator />
            <Alert.Content gap="2">
              <Alert.Title>{turn.error}</Alert.Title>
              {turn.unsent && (
                <Button
                  size="xs"
                  variant="outline"
                  alignSelf="flex-start"
                  onClick={() => onSend(turn.user)}
                >
                  Send again
                </Button>
              )}
            </Alert.Content>
          </Alert.Root>
        )}
        <div ref={end} />
      </Box>
      <Composer streaming={streaming} onSend={onSend} onStop={onStop} />
      <Text fontSize="xs" color="fg.muted" textAlign="center">
        Answers can be wrong. Don't share personal information; the demo uses Gemini's free tier.
      </Text>
    </Stack>
  )
}
