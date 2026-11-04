import {
  Box,
  Button,
  HStack,
  IconButton,
  Input,
  Menu,
  Portal,
  SegmentGroup,
  Stack,
  Text,
} from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { useState } from "react"
import {
  LuArchive,
  LuArchiveRestore,
  LuEllipsis,
  LuPencil,
  LuPlus,
  LuStar,
  LuTrash2,
} from "react-icons/lu"
import {
  chatDeleteConversationMutation,
  chatListConversationsOptions,
  chatUpdateConversationMutation,
} from "@/client/@tanstack/react-query.gen"
import type { ConversationRead } from "@/client/types.gen"
import { ConfirmDialog } from "@/components/ConfirmDialog"
import { ErrorState, ListSkeleton } from "@/components/States"
import { formatRelative } from "@/lib/format"
import { invalidateOperations } from "@/lib/queryKeys"

export function ConversationList({
  selectedId,
  onNew,
  onDeleted,
}: {
  selectedId?: string
  onNew: () => void
  onDeleted: (id: string) => void
}) {
  const queryClient = useQueryClient()
  const [archived, setArchived] = useState(false)
  const [renaming, setRenaming] = useState<string | null>(null)
  const [deleting, setDeleting] = useState<ConversationRead | null>(null)
  const query = useQuery(chatListConversationsOptions({ query: { archived, limit: 100 } }))
  const refresh = () => invalidateOperations(queryClient, "chatListConversations")
  const update = useMutation({
    ...chatUpdateConversationMutation(),
    meta: { errorTitle: "Couldn't update" },
    onSuccess: refresh,
  })
  const remove = useMutation({
    ...chatDeleteConversationMutation(),
    meta: { errorTitle: "Couldn't delete" },
    onSuccess: (_data, variables) => {
      onDeleted(variables.path.conversation_id)
      return refresh()
    },
  })
  const patch = (id: string, body: Parameters<typeof update.mutate>[0]["body"]) =>
    update.mutate({ path: { conversation_id: id }, body })

  return (
    <Stack gap="3" h="full">
      <Button colorPalette="brand" onClick={onNew}>
        <LuPlus /> New chat
      </Button>
      <SegmentGroup.Root
        size="sm"
        value={archived ? "archived" : "active"}
        onValueChange={(details) => setArchived(details.value === "archived")}
        aria-label="Show conversations"
      >
        <SegmentGroup.Indicator />
        <SegmentGroup.Items
          items={[
            { value: "active", label: "Active" },
            { value: "archived", label: "Archived" },
          ]}
        />
      </SegmentGroup.Root>
      {query.isPending ? (
        <ListSkeleton rows={4} height="52px" />
      ) : query.isError ? (
        <ErrorState
          error={query.error}
          title="Couldn't load conversations"
          onRetry={() => query.refetch()}
        />
      ) : query.data.items.length === 0 ? (
        <Text fontSize="sm" color="fg.muted" px="1">
          {archived
            ? "No archived conversations."
            : "No conversations yet. Ask anything about your trips."}
        </Text>
      ) : (
        <Stack as="ul" gap="1" listStyleType="none" overflowY="auto" aria-label="Conversations">
          {query.data.items.map((conversation) => {
            const active = conversation.id === selectedId
            return (
              <HStack
                as="li"
                key={conversation.id}
                gap="1"
                borderRadius="md"
                bg={active ? "bg.panel" : "transparent"}
                boxShadow={active ? "card" : "none"}
                pe="1"
              >
                {renaming === conversation.id ? (
                  <Box asChild flex="1" p="1">
                    <form
                      onSubmit={(event) => {
                        event.preventDefault()
                        const title = new FormData(event.currentTarget)
                          .get("title")
                          ?.toString()
                          .trim()
                        if (title) patch(conversation.id, { title })
                        setRenaming(null)
                      }}
                    >
                      <Input
                        name="title"
                        size="sm"
                        defaultValue={conversation.title}
                        maxLength={200}
                        aria-label="Conversation title"
                        autoFocus
                        onBlur={() => setRenaming(null)}
                      />
                    </form>
                  </Box>
                ) : (
                  <Link
                    to="/assistant"
                    search={{ c: conversation.id }}
                    style={{ flex: 1, minWidth: 0 }}
                    aria-current={active ? "page" : undefined}
                  >
                    <Stack gap="0" px="2" py="2" minH="44px" justify="center">
                      <HStack gap="1">
                        {conversation.is_favorite && (
                          <>
                            <LuStar
                              aria-hidden="true"
                              fill="currentColor"
                              color="var(--chakra-colors-brand-solid)"
                            />
                            <Text srOnly>Favourite:</Text>
                          </>
                        )}
                        <Text fontSize="sm" fontWeight={active ? "600" : "500"} truncate>
                          {conversation.title}
                        </Text>
                      </HStack>
                      <Text fontSize="xs" color="fg.muted">
                        {formatRelative(conversation.last_message_at)}
                      </Text>
                    </Stack>
                  </Link>
                )}
                <Menu.Root positioning={{ placement: "bottom-end" }}>
                  <Menu.Trigger asChild>
                    <IconButton
                      size="sm"
                      variant="ghost"
                      aria-label={`Actions for ${conversation.title}`}
                    >
                      <LuEllipsis />
                    </IconButton>
                  </Menu.Trigger>
                  <Portal>
                    <Menu.Positioner>
                      <Menu.Content>
                        <Menu.Item
                          value="favorite"
                          onSelect={() =>
                            patch(conversation.id, { is_favorite: !conversation.is_favorite })
                          }
                        >
                          <LuStar /> {conversation.is_favorite ? "Remove favourite" : "Favourite"}
                        </Menu.Item>
                        <Menu.Item value="rename" onSelect={() => setRenaming(conversation.id)}>
                          <LuPencil /> Rename
                        </Menu.Item>
                        <Menu.Item
                          value="archive"
                          onSelect={() =>
                            patch(conversation.id, { is_archived: !conversation.is_archived })
                          }
                        >
                          {conversation.is_archived ? <LuArchiveRestore /> : <LuArchive />}
                          {conversation.is_archived ? "Unarchive" : "Archive"}
                        </Menu.Item>
                        <Menu.Item
                          value="delete"
                          color="fg.error"
                          onSelect={() => setDeleting(conversation)}
                        >
                          <LuTrash2 /> Delete
                        </Menu.Item>
                      </Menu.Content>
                    </Menu.Positioner>
                  </Portal>
                </Menu.Root>
              </HStack>
            )
          })}
        </Stack>
      )}
      <ConfirmDialog
        open={deleting !== null}
        onOpenChange={(open) => !open && setDeleting(null)}
        title="Delete this conversation?"
        description={`“${deleting?.title ?? ""}” and its messages will be deleted.`}
        confirmLabel="Delete"
        destructive
        loading={remove.isPending}
        onConfirm={() =>
          deleting &&
          remove.mutate(
            { path: { conversation_id: deleting.id } },
            { onSettled: () => setDeleting(null) },
          )
        }
      />
    </Stack>
  )
}
