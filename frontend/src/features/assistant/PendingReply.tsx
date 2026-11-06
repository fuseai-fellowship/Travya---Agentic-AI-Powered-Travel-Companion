import { Box, HStack, Icon, Stack, Text } from "@chakra-ui/react"
import { LuCheck } from "react-icons/lu"
import { Markdown } from "@/components/Markdown"
import { formatElapsed } from "@/lib/format"
import { useNow } from "@/lib/hooks"
import { isWorking, type PendingTurn } from "./useChat"

/** After this long without a token, say why it is slow. */
export const SLOW_AFTER_MS = 10_000

function TypingDots() {
  return (
    <HStack gap="1" aria-hidden="true" h="2" data-testid="typing">
      {[0, 1, 2].map((index) => (
        <Box
          key={index}
          boxSize="1.5"
          borderRadius="full"
          bg="fg.muted"
          animation="travya-pulse 1.2s ease-in-out infinite"
          style={{ animationDelay: `${index * 160}ms` }}
        />
      ))}
    </HStack>
  )
}

function statusLabel(turn: PendingTurn): string {
  if (turn.phase === "sending") return "Sending"
  const lastTool = turn.tools.at(-1)
  return lastTool ? lastTool.replace(/…$/, "") : "Thinking"
}

/** The assistant's side of the turn in flight: what it is doing, for how long, then the reply. */
export function PendingReply({ turn }: { turn: PendingTurn }) {
  const working = isWorking(turn)
  const now = useNow(working, 500)
  const elapsed = now - turn.startedAt
  const waiting = working && !turn.reply
  const steps = [...new Set(turn.tools)]

  if (!working && !turn.reply && turn.phase !== "stopped") return null

  return (
    <Stack as="li" gap="1.5" align="flex-start" listStyleType="none" aria-busy={working}>
      <Text srOnly>Travya is replying:</Text>
      {steps.length > 0 && (
        <Stack as="ul" gap="0.5" listStyleType="none" aria-label="Steps">
          {steps.map((step, index) => {
            const done = !waiting || index < steps.length - 1
            return (
              <HStack as="li" key={step} gap="1.5" fontSize="xs" color="fg.muted">
                {done ? (
                  <Icon as={LuCheck} color="sea.fg" aria-hidden="true" />
                ) : (
                  <Box boxSize="1.5" mx="1" borderRadius="full" bg="brand.solid" />
                )}
                <Text as="span">{done ? step.replace(/…$/, "") : step}</Text>
              </HStack>
            )
          })}
        </Stack>
      )}
      <Box
        maxW={{ base: "92%", md: "80%" }}
        px="4"
        py="2.5"
        borderRadius="card"
        bg="bg.panel"
        borderWidth="1px"
      >
        {turn.reply ? (
          <Markdown>{turn.reply}</Markdown>
        ) : turn.phase === "stopped" ? (
          <Text fontSize="sm" color="fg.muted">
            Stopped before a reply.
          </Text>
        ) : (
          <HStack gap="3" minH="6">
            <TypingDots />
            <Text fontSize="sm" color="fg.muted">
              {statusLabel(turn)}…
            </Text>
          </HStack>
        )}
      </Box>
      <HStack gap="2" fontSize="xs" color="fg.muted" ps="1">
        {working && (
          <Text as="span" fontFamily="mono" style={{ fontVariantNumeric: "tabular-nums" }}>
            {formatElapsed(elapsed)}
          </Text>
        )}
        {turn.phase === "stopped" && turn.reply && <Text as="span">Stopped</Text>}
        {waiting && elapsed >= SLOW_AFTER_MS && (
          <Text as="span">
            Still working. The free-tier model can take about 30&nbsp;s, longer when it is busy.
          </Text>
        )}
      </HStack>
    </Stack>
  )
}
