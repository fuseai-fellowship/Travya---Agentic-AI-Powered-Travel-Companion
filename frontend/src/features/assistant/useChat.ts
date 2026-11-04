import { useQueryClient } from "@tanstack/react-query"
import { useCallback, useState } from "react"
import { apiFetch, apiUrl } from "@/lib/api"
import { ApiError } from "@/lib/errors"
import { notifyError } from "@/lib/notify"
import { invalidateOperations } from "@/lib/queryKeys"
import { useEventStream } from "@/lib/sse"

export interface PendingTurn {
  conversationId: string
  user: string
  reply: string
  tools: string[]
  error: string | null
  /** True when the API refused the message before streaming (nothing was saved). */
  unsent: boolean
}

/** Sends one message and streams the reply; persisted messages are refetched when it finishes. */
export function useChat() {
  const queryClient = useQueryClient()
  const stream = useEventStream(apiFetch)
  const [pending, setPending] = useState<PendingTurn | null>(null)

  const send = useCallback(
    async (conversationId: string, content: string) => {
      setPending({
        conversationId,
        user: content,
        reply: "",
        tools: [],
        error: null,
        unsent: false,
      })
      const update = (change: (turn: PendingTurn) => PendingTurn) =>
        setPending((turn) => (turn && turn.conversationId === conversationId ? change(turn) : turn))

      const outcome = await stream.start(
        apiUrl(`/api/v1/conversations/${conversationId}/messages`),
        { content },
        (event) => {
          if (event.kind === "token")
            update((turn) => ({ ...turn, reply: turn.reply + event.message }))
          else if (event.kind === "progress")
            update((turn) => ({ ...turn, tools: [...turn.tools, event.message] }))
          else if (event.kind === "error") update((turn) => ({ ...turn, error: event.message }))
        },
      )

      if (outcome instanceof ApiError) {
        notifyError(outcome, "Message not sent")
        update((turn) => ({ ...turn, error: outcome.detail, unsent: !turn.reply }))
        return
      }
      await invalidateOperations(queryClient, "chatListMessages", "chatListConversations")
      setPending((turn) =>
        turn && turn.conversationId === conversationId && !turn.error ? null : turn,
      )
    },
    [queryClient, stream],
  )

  return {
    send,
    pending,
    streaming: stream.status === "streaming",
    stop: stream.abort,
    clear: () => setPending(null),
  }
}
