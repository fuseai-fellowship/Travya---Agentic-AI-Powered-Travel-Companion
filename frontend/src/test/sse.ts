import type { AgentEvent } from "@/lib/sse"

const encoder = new TextEncoder()

export const frame = (event: Partial<AgentEvent> & Pick<AgentEvent, "kind">) =>
  `event: ${event.kind}\ndata: ${JSON.stringify({ agent: "travya", message: "", data: null, ...event })}\n\n`

/**
 * A text/event-stream body: `before` is sent at once, `after` once `gate` resolves (left open
 * forever when `gate` never resolves, like a slow model).
 */
export function sseBody(before: string[], after: string[] = [], gate?: Promise<void>) {
  return new ReadableStream<Uint8Array>({
    async start(controller) {
      for (const chunk of before) controller.enqueue(encoder.encode(chunk))
      if (gate) await gate
      for (const chunk of after) controller.enqueue(encoder.encode(chunk))
      controller.close()
    },
  })
}

export const SSE_HEADERS = { "Content-Type": "text/event-stream" }

/** A promise plus its resolve function, for holding a stream open. */
export function deferred() {
  let resolve: () => void = () => undefined
  const promise = new Promise<void>((done) => {
    resolve = done
  })
  return { promise, resolve }
}

/** Firebase stand-in for components that call the API (`vi.mock("@/lib/firebase", () => firebaseMock)`). */
export const firebaseMock = {
  auth: {},
  currentUser: async () => null,
  onSessionExpired: () => () => undefined,
  firebaseTokens: { getToken: async () => "test-token", onUnauthorized: () => undefined },
}
