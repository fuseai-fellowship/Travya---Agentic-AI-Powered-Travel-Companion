import { Box, Button, Field, Flex, Heading, HStack, NativeSelect, Stack } from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { getRouteApi } from "@tanstack/react-router"
import { useState } from "react"
import { LuArrowLeft } from "react-icons/lu"
import {
  chatCreateConversationMutation,
  chatListConversationsOptions,
  chatUpdateConversationMutation,
  tripsListTripsOptions,
} from "@/client/@tanstack/react-query.gen"
import { useDocumentTitle } from "@/lib/hooks"
import { invalidateOperations } from "@/lib/queryKeys"
import { ConversationList } from "./ConversationList"
import { Thread } from "./Thread"
import { useChat } from "./useChat"

const route = getRouteApi("/_app/assistant")

export function AssistantPage() {
  useDocumentTitle("Assistant")
  const { c: conversationId, trip: tripParam } = route.useSearch()
  const navigate = route.useNavigate()
  const queryClient = useQueryClient()
  const chat = useChat()
  const [draftTripId, setDraftTripId] = useState(tripParam ?? "")
  // Mobile shows either the list or the thread; "New chat" opens an empty thread.
  const [composing, setComposing] = useState(Boolean(tripParam))

  const trips = useQuery(tripsListTripsOptions({ query: { limit: 100 } }))
  const active = useQuery(chatListConversationsOptions({ query: { archived: false, limit: 100 } }))
  const archived = useQuery({
    ...chatListConversationsOptions({ query: { archived: true, limit: 100 } }),
    enabled: Boolean(conversationId),
  })
  const conversation = [...(active.data?.items ?? []), ...(archived.data?.items ?? [])].find(
    (item) => item.id === conversationId,
  )
  const tripId = conversationId ? (conversation?.trip_id ?? "") : draftTripId
  const destination = trips.data?.items.find((trip) => trip.id === tripId)?.destination

  const create = useMutation({
    ...chatCreateConversationMutation(),
    meta: { errorTitle: "Couldn't start a conversation" },
  })
  const update = useMutation({
    ...chatUpdateConversationMutation(),
    meta: { errorTitle: "Couldn't change the trip" },
    onSuccess: () => invalidateOperations(queryClient, "chatListConversations"),
  })

  const send = async (content: string) => {
    let id = conversationId
    if (!id) {
      const created = await create
        .mutateAsync({ body: { trip_id: draftTripId || null } })
        .catch(() => null)
      if (!created) return
      id = created.id
      void invalidateOperations(queryClient, "chatListConversations")
      await navigate({ search: { c: id } })
    }
    await chat.send(id, content)
  }

  const changeTrip = (value: string) => {
    if (conversationId)
      update.mutate({ path: { conversation_id: conversationId }, body: { trip_id: value || null } })
    else setDraftTripId(value)
  }

  const noConversations = active.data?.items.length === 0 && !conversationId
  const showThreadOnMobile =
    Boolean(conversationId) || chat.pending !== null || composing || noConversations
  const backToList = () => {
    setComposing(false)
    void navigate({ search: {} })
  }

  return (
    <Flex h={{ base: "calc(100dvh - 56px - 72px)", lg: "100dvh" }} minH="480px">
      <Box
        as="aside"
        aria-label="Conversations"
        w={{ base: "full", md: "300px" }}
        flexShrink={0}
        borderRightWidth={{ md: "1px" }}
        p="4"
        display={{ base: showThreadOnMobile ? "none" : "block", md: "block" }}
        overflowY="auto"
      >
        <ConversationList
          selectedId={conversationId}
          onNew={() => {
            chat.clear()
            setComposing(true)
            void navigate({ search: {} })
          }}
          onDeleted={(id) => id === conversationId && navigate({ search: {} })}
        />
      </Box>
      <Stack
        flex="1"
        minW="0"
        p={{ base: "3", md: "6" }}
        gap="3"
        display={{ base: showThreadOnMobile ? "flex" : "none", md: "flex" }}
      >
        <HStack justify="space-between" gap="3" flexWrap="wrap">
          <HStack gap="2" minW="0">
            <Button
              display={{ base: noConversations ? "none" : "inline-flex", md: "none" }}
              size="sm"
              variant="ghost"
              aria-label="Back to conversations"
              onClick={backToList}
            >
              <LuArrowLeft />
            </Button>
            <Heading as="h1" fontFamily="heading" size="xl" truncate>
              {conversation?.title ?? "New conversation"}
            </Heading>
          </HStack>
          <Field.Root w={{ base: "full", sm: "260px" }}>
            <Field.Label srOnly>Trip context</Field.Label>
            <NativeSelect.Root size="sm">
              <NativeSelect.Field
                value={tripId}
                onChange={(event) => changeTrip(event.target.value)}
                aria-label="Trip context"
              >
                <option value="">No trip context</option>
                {(trips.data?.items ?? []).map((trip) => (
                  <option key={trip.id} value={trip.id}>
                    {trip.destination} · {trip.title}
                  </option>
                ))}
              </NativeSelect.Field>
              <NativeSelect.Indicator />
            </NativeSelect.Root>
          </Field.Root>
        </HStack>
        <Box flex="1" minH="0">
          <Thread
            conversationId={conversationId}
            pending={chat.pending}
            creating={create.isPending}
            announcement={chat.announcement}
            destination={destination}
            onSend={(content) => void send(content)}
            onStop={chat.stop}
          />
        </Box>
      </Stack>
    </Flex>
  )
}
