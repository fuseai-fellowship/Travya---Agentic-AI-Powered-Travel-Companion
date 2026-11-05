import { Box, Heading, HStack, IconButton, Link, List, Stack, Text } from "@chakra-ui/react"
import { useMutation } from "@tanstack/react-query"
import { useState } from "react"
import { LuExternalLink, LuThumbsDown, LuThumbsUp } from "react-icons/lu"
import { feedbackGiveFeedbackMutation } from "@/client/@tanstack/react-query.gen"
import { formatMoney } from "@/lib/format"
import { notifySuccess } from "@/lib/notify"
import type { PlanView } from "./plan"

function TipList({ title, tips }: { title: string; tips: string[] }) {
  if (!tips.length) return null
  return (
    <Box>
      <Heading as="h3" size="sm" mb="1.5">
        {title}
      </Heading>
      <List.Root gap="1" ps="5" fontSize="sm">
        {tips.map((tip) => (
          <List.Item key={tip}>{tip}</List.Item>
        ))}
      </List.Root>
    </Box>
  )
}

export function PlanDetails({
  plan,
  tripId,
  currency,
}: {
  plan: PlanView
  tripId: string
  currency: string
}) {
  const [rated, setRated] = useState<number | null>(null)
  const feedback = useMutation({
    ...feedbackGiveFeedbackMutation(),
    meta: { errorTitle: "Couldn't send feedback" },
  })
  const rate = (rating: number) =>
    feedback.mutate(
      { body: { target_type: "trip_plan", target_id: tripId, rating } },
      {
        onSuccess: () => {
          setRated(rating)
          notifySuccess("Thanks for the feedback")
        },
      },
    )

  return (
    <Stack gap="5" p="4" borderWidth="1px" borderRadius="card" bg="bg.panel">
      {plan.summary && (
        <Text fontFamily="heading" fontSize="lg" lineHeight="1.5">
          {plan.summary}
        </Text>
      )}
      {plan.breakdown.length > 0 && (
        <HStack gap="4" flexWrap="wrap" fontSize="sm">
          {plan.breakdown.map(([key, value]) => (
            <Text key={key} color="fg.muted" textTransform="capitalize">
              {key}{" "}
              <Text
                as="span"
                fontFamily="mono"
                color="fg"
                style={{ fontVariantNumeric: "tabular-nums" }}
              >
                {formatMoney(value, currency)}
              </Text>
            </Text>
          ))}
        </HStack>
      )}
      <TipList title="Local tips" tips={plan.localTips} />
      <TipList title="Packing" tips={plan.packingTips} />
      {plan.sources.length > 0 && (
        <Box>
          <Heading as="h3" size="sm" mb="1.5">
            Sources
          </Heading>
          <List.Root gap="1" ps="5" fontSize="sm">
            {plan.sources.map((source) => (
              <List.Item key={source.url}>
                <Link href={source.url} target="_blank" rel="noopener noreferrer" color="brand.fg">
                  {source.title} <LuExternalLink aria-hidden="true" />
                </Link>
              </List.Item>
            ))}
          </List.Root>
        </Box>
      )}
      <HStack gap="2" fontSize="sm" color="fg.muted">
        <Text>Was this plan useful?</Text>
        <IconButton
          size="sm"
          variant={rated === 5 ? "solid" : "ghost"}
          aria-label="Yes, useful"
          aria-pressed={rated === 5}
          disabled={feedback.isPending}
          onClick={() => rate(5)}
        >
          <LuThumbsUp />
        </IconButton>
        <IconButton
          size="sm"
          variant={rated === 1 ? "solid" : "ghost"}
          aria-label="No, not useful"
          aria-pressed={rated === 1}
          disabled={feedback.isPending}
          onClick={() => rate(1)}
        >
          <LuThumbsDown />
        </IconButton>
      </HStack>
    </Stack>
  )
}
