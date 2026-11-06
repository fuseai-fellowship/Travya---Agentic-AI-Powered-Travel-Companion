import { Alert, Button } from "@chakra-ui/react"
import { useQueryClient } from "@tanstack/react-query"
import { wakeApi } from "@/lib/api"
import { useNow } from "@/lib/hooks"
import { useWakeStatus } from "@/lib/wake"

/** Shown while the free API server wakes up after a quiet spell, instead of "offline" errors. */
export function WakeBanner() {
  const { status, since } = useWakeStatus()
  const queryClient = useQueryClient()
  const now = useNow(status === "waking", 1000)
  if (status === "waking") {
    const seconds = since === null ? 0 : Math.max(0, Math.round((now - since) / 1000))
    return (
      <Alert.Root status="info" borderRadius="0" borderBottomWidth="1px" role="status">
        <Alert.Indicator />
        <Alert.Content>
          <Alert.Title>Waking up the free server…</Alert.Title>
          <Alert.Description>
            The demo's server sleeps when nobody uses it and takes up to a minute to start.{" "}
            <span style={{ fontVariantNumeric: "tabular-nums" }}>{seconds} s</span>
          </Alert.Description>
        </Alert.Content>
      </Alert.Root>
    )
  }
  if (status === "failed") {
    return (
      <Alert.Root status="warning" borderRadius="0" borderBottomWidth="1px" role="status">
        <Alert.Indicator />
        <Alert.Content>
          <Alert.Title>The server didn't wake up</Alert.Title>
          <Alert.Description>It may be restarting. Try again in a minute.</Alert.Description>
        </Alert.Content>
        <Button
          size="sm"
          variant="outline"
          onClick={async () => {
            if (await wakeApi()) await queryClient.invalidateQueries()
          }}
        >
          Try again
        </Button>
      </Alert.Root>
    )
  }
  return null
}
