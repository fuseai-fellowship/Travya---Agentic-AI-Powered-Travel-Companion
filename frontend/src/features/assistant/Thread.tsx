import { Alert, Box, Button, Heading, Stack, Text, Wrap } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { useEffect, useRef } from "react"
import { LuMessageCircle, LuRefreshCw } from "react-icons/lu"
import { chatListMessagesOptions } from "@/client/@tanstack/react-query.gen"
import { ErrorState, ListSkeleton } from "@/components/States"
import { Composer } from "./Composer"
import { MessageBubble } from "./MessageBubble"
import { PendingReply } from "./PendingReply"
import { isWorking, type PendingTurn } from "./useChat"

/** The API returns messages oldest first; long threads show their latest page. */
export const PAGE = 200

export function suggestedPrompts(destination?: string): string[] {
  const place = destination ?? "Kathmandu"
  return [
    `What should I pack for ${place} next month?`,
    `Find vegetarian-friendly places to eat in ${place}`,
    `What's a good rainy-day plan in ${place}?`,
  ]
}

function useLatestMessages(conversationId?: string) {
  const first = useQuery({
    ...chatListMessagesOptions({
      path: { conversation_id: conversationId ?? "" },
      query: { limit: PAGE },
    }),
    enabled: Boolean(conversationId),
  })
  const offset = Math.max(0, (first.data?.total ?? 0) - PAGE)
  const latest = useQuery({
    ...chatListMessagesOptions({
      path: { conversation_id: conversationId ?? "" },
      query: { limit: PAGE, offset },
    }),
    enabled: Boolean(conversationId) && offset > 0,
  })
  return offset > 0
    ? { query: latest, items: latest.data?.items ?? [], older: offset }
    : { query: first, items: first.data?.items ?? [], older: 0 }
}

export function Thread({
  conversationId,
  pending,
  creating = false,
  announcement = "",
  destination,
  onSend,
  onStop,
}: {
  conversationId?: string
  pending: PendingTurn | null
  /** The conversation itself is still being created. */
  creating?: boolean
  /** Polite announcement of the finished reply (the log itself stays quiet while streaming). */
  announcement?: string
  destination?: string
  onSend: (content: string) => void
  onStop: () => void
}) {
  const { query: messages, items: loaded, older } = useLatestMessages(conversationId)
  const end = useRef<HTMLDivElement>(null)
  const turn =
    pending && (!conversationId || pending.conversationId === conversationId) ? pending : null
  const items = conversationId ? loaded : []
  const working = isWorking(turn)
  const busy = creating || working

  // biome-ignore lint/correctness/useExhaustiveDependencies: scroll as the reply streams in
  useEffect(() => {
    end.current?.scrollIntoView({ block: "end" })
  }, [items.length, turn?.reply, turn?.tools.length, turn?.phase])

  const empty = !items.length && !turn

  return (
    <Stack h="full" gap="3" minH="0">
      <Box flex="1" overflowY="auto" minH="0" px={{ base: "0", md: "2" }}>
        {conversationId && messages.isPending && !turn ? (
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
            <Heading as="h2" size="xl">
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
                  disabled={busy}
                  onClick={() => onSend(prompt)}
                >
                  {prompt}
                </Button>
              ))}
            </Wrap>
          </Stack>
        ) : (
          <>
            {older > 0 && (
              <Text fontSize="xs" color="fg.muted" textAlign="center" py="2">
                Showing the latest {PAGE} messages.
              </Text>
            )}
            <Stack as="ol" gap="4" py="2" role="log" aria-live="off" aria-label="Conversation">
              {items.map((message) => (
                <MessageBubble
                  key={message.id}
                  id={message.id}
                  author={message.role}
                  content={message.content}
                  tools={Array.isArray(message.meta?.tools) ? (message.meta.tools as string[]) : []}
                  interrupted={message.meta?.interrupted === true}
                />
              ))}
              {turn && (
                <>
                  {!turn.saved && <MessageBubble author="user" content={turn.user} />}
                  <PendingReply turn={turn} />
                </>
              )}
            </Stack>
          </>
        )}
        {turn?.phase === "error" && turn.error && (
          <Alert.Root status="error" mt="3" borderRadius="card" role="alert">
            <Alert.Indicator />
            <Alert.Content gap="2">
              <Alert.Title>{turn.error}</Alert.Title>
              <Button
                size="xs"
                variant="outline"
                alignSelf="flex-start"
                onClick={() => onSend(turn.user)}
              >
                <LuRefreshCw /> Retry
              </Button>
            </Alert.Content>
          </Alert.Root>
        )}
        <div ref={end} />
      </Box>
      <Text srOnly role="status" aria-live="polite">
        {announcement}
      </Text>
      <Composer
        state={creating ? "creating" : working ? "working" : "idle"}
        onSend={onSend}
        onStop={onStop}
      />
      <Text fontSize="xs" color="fg.muted" textAlign="center">
        Answers can be wrong. Don't share personal information; the demo uses Gemini's free tier.
      </Text>
    </Stack>
  )
}
