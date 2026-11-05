import { useQueryClient } from "@tanstack/react-query"
import { useCallback, useState } from "react"
import { apiFetch, apiUrl } from "@/lib/api"
import { reportDemoLimit } from "@/lib/demoLimit"
import { ApiError, errorMessage } from "@/lib/errors"
import { invalidateOperations } from "@/lib/queryKeys"
import { useEventStream } from "@/lib/sse"

/**
 * sending: request in flight, nothing back yet · waiting: the API saved the message and the model
 * is working · streaming: tokens arriving · stopped: aborted by the user · error: failed.
 */
export type TurnPhase = "sending" | "waiting" | "streaming" | "stopped" | "error"

export interface PendingTurn {
  conversationId: string
  user: string
  reply: string
  /** Tool steps in arrival order, e.g. "Checking the weather…". */
  tools: string[]
  phase: TurnPhase
  startedAt: number
  error: string | null
  /** The API stored the user's message, so the refetched thread already shows it. */
  saved: boolean
}

export const isWorking = (turn: PendingTurn | null) =>
  turn !== null &&
  (turn.phase === "sending" || turn.phase === "waiting" || turn.phase === "streaming")

const DROPPED = "The connection dropped before the reply finished. Your message was saved."

/** Plain text for the screen-reader announcement of a finished reply. */
export function speakable(markdown: string): string {
  const text = markdown
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/\]\([^)]*\)/g, "]")
    .replace(/[*_`#>[\]]/g, "")
    .replace(/\s+/g, " ")
    .trim()
  return text.length > 400 ? `${text.slice(0, 400)}…` : text
}

/** Sends one message and streams the reply; persisted messages are refetched when it ends. */
export function useChat() {
  const queryClient = useQueryClient()
  const stream = useEventStream(apiFetch)
  const [pending, setPending] = useState<PendingTurn | null>(null)
  const [announcement, setAnnouncement] = useState("")

  const send = useCallback(
    async (conversationId: string, content: string) => {
      setAnnouncement("")
      setPending({
        conversationId,
        user: content,
        reply: "",
        tools: [],
        phase: "sending",
        startedAt: Date.now(),
        error: null,
        saved: false,
      })
      const update = (change: (turn: PendingTurn) => PendingTurn) =>
        setPending((turn) => (turn && turn.conversationId === conversationId ? change(turn) : turn))
      const refetch = () =>
        invalidateOperations(queryClient, "chatListMessages", "chatListConversations")

      // Written from the stream callbacks; an object keeps TypeScript from narrowing them away.
      const run: { opened: boolean; reply: string; failure: string | null } = {
        opened: false,
        reply: "",
        failure: null,
      }
      const outcome = await stream.start(
        apiUrl(`/api/v1/conversations/${conversationId}/messages`),
        { content },
        (event) => {
          if (event.kind === "token") {
            run.reply += event.message
            const reply = run.reply
            update((turn) => ({ ...turn, phase: "streaming", reply }))
          } else if (event.kind === "progress") {
            update((turn) => ({ ...turn, tools: [...turn.tools, event.message] }))
          } else if (event.kind === "error") {
            run.failure = event.message || "The assistant couldn't answer."
          }
        },
        () => {
          // The API commits the user's message before it opens the stream.
          run.opened = true
          update((turn) => ({ ...turn, phase: "waiting" }))
        },
      )

      if (outcome instanceof ApiError) {
        if (outcome.kind === "demo_limit") reportDemoLimit(outcome.detail)
        if (run.opened) await refetch()
        update((turn) => ({
          ...turn,
          phase: "error",
          saved: run.opened,
          error: run.opened ? DROPPED : errorMessage(outcome),
        }))
        return
      }

      await refetch()
      if (outcome === "aborted") {
        update((turn) => ({ ...turn, phase: "stopped", saved: run.opened }))
        setAnnouncement("Stopped.")
        return
      }
      if (run.failure) {
        const error = run.failure
        update((turn) => ({ ...turn, phase: "error", saved: true, error }))
        return
      }
      setPending((turn) => (turn && turn.conversationId === conversationId ? null : turn))
      setAnnouncement(run.reply ? `Travya replied: ${speakable(run.reply)}` : "")
    },
    [queryClient, stream],
  )

  return {
    send,
    pending,
    working: isWorking(pending),
    announcement,
    stop: stream.abort,
    clear: () => setPending(null),
  }
}
