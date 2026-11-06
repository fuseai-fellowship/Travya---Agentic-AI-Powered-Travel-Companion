import { Box, Container, Heading, SegmentGroup, Skeleton, Stack, Text } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import type { ReactNode } from "react"
import { accountReadMeOptions, accountUsageOptions } from "@/client/@tanstack/react-query.gen"
import { ErrorState } from "@/components/States"
import { useColorMode } from "@/components/ui/color-mode"
import { useAuth } from "@/features/auth/AuthProvider"
import { plural } from "@/lib/format"
import { useDocumentTitle } from "@/lib/hooks"
import { DeleteAccount } from "./DeleteAccount"
import { ProfileForm } from "./ProfileForm"
import { UpgradeAccount } from "./UpgradeAccount"

function Section({ title, children }: { title: string; children: ReactNode }) {
  const id = `settings-${title.toLowerCase().replace(/\W+/g, "-")}`
  return (
    <Box
      as="section"
      aria-labelledby={id}
      p={{ base: "4", md: "6" }}
      bg="bg.panel"
      borderWidth="1px"
      borderRadius="card"
    >
      <Heading as="h2" id={id} fontFamily="heading" size="lg" mb="4">
        {title}
      </Heading>
      {children}
    </Box>
  )
}

export function SettingsPage() {
  useDocumentTitle("Settings")
  const { user } = useAuth()
  const me = useQuery(accountReadMeOptions())
  const usage = useQuery(accountUsageOptions())
  const { preference, setColorMode } = useColorMode()

  return (
    <Container maxW="3xl" py={{ base: "6", md: "10" }} px={{ base: "4", md: "8" }}>
      <Stack gap="6">
        <Heading as="h1" fontFamily="heading" size="3xl" fontWeight="600">
          Settings
        </Heading>

        <Section title="Profile">
          {me.isPending ? (
            <Skeleton h="180px" />
          ) : me.isError ? (
            <ErrorState
              error={me.error}
              title="Couldn't load your profile"
              onRetry={() => me.refetch()}
            />
          ) : (
            <ProfileForm me={me.data} />
          )}
        </Section>

        <Section title="Account">{user && <UpgradeAccount user={user} />}</Section>

        <Section title="Usage today">
          {usage.isPending ? (
            <Skeleton h="6" w="60%" />
          ) : usage.isError ? (
            <ErrorState
              error={usage.error}
              title="Couldn't load usage"
              onRetry={() => usage.refetch()}
            />
          ) : (
            <UsageLine usage={usage.data} />
          )}
        </Section>

        <Section title="Appearance">
          <SegmentGroup.Root
            value={preference}
            onValueChange={(details) => details.value && setColorMode(details.value)}
            aria-label="Colour mode"
          >
            <SegmentGroup.Indicator />
            <SegmentGroup.Items
              items={[
                { value: "light", label: "Light" },
                { value: "dark", label: "Dark" },
                { value: "system", label: "System" },
              ]}
            />
          </SegmentGroup.Root>
        </Section>

        <Section title="Privacy">
          <Text fontSize="sm" color="fg.muted">
            The demo uses Gemini's free tier, so don't enter personal information in trips, notes or
            chats. Map data © OpenStreetMap contributors; guides from Wikivoyage (CC BY-SA); weather
            by Open-Meteo. Bookings are simulated.
          </Text>
        </Section>

        <Section title="Delete account">
          <DeleteAccount />
        </Section>
      </Stack>
    </Container>
  )
}

/**
 * The budget counts model calls; a plan or chat turn takes several, so runs are an estimate.
 * (`llm_calls_*` arrive with the backend review changes; older APIs only send runs.)
 */
function UsageLine({ usage }: { usage: { llm_runs_remaining_today: number } }) {
  const extra = usage as { llm_calls_remaining_today?: unknown; llm_calls_per_day?: unknown }
  const calls =
    typeof extra.llm_calls_remaining_today === "number" ? extra.llm_calls_remaining_today : null
  const perDay = typeof extra.llm_calls_per_day === "number" ? extra.llm_calls_per_day : null
  return (
    <Text>
      {calls !== null ? "About " : ""}
      <Text as="span" fontWeight="700" style={{ fontVariantNumeric: "tabular-nums" }}>
        {plural(usage.llm_runs_remaining_today, "agent run")}
      </Text>{" "}
      left today in the shared demo budget
      {calls !== null &&
        ` (${calls}${perDay !== null ? ` of ${perDay}` : ""} model calls; a plan uses several)`}
      . It resets daily.
    </Text>
  )
}
