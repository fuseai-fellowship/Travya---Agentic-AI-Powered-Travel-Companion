import { Box, Heading, HStack, SimpleGrid, Stack, Text } from "@chakra-ui/react"
import { useEffect, useRef, useState } from "react"
import { formatElapsed, formatMoney } from "@/lib/format"
import { usePrefersReducedMotion } from "@/lib/hooks"
import { dayColor } from "@/theme/dayColors"
import kathmanduDark from "./media/gallery-kathmandu-dark.webp"
import kathmanduLight from "./media/gallery-kathmandu-light.webp"
import kyotoDark from "./media/gallery-kyoto-dark.webp"
import kyotoLight from "./media/gallery-kyoto-light.webp"
import lisbonDark from "./media/gallery-lisbon-dark.webp"
import lisbonLight from "./media/gallery-lisbon-light.webp"
import { RunMap } from "./RunMap"
import { GALLERY, type GalleryPlan, recordedOn } from "./runs"
import { Section } from "./Section"

const BASEMAPS: Record<string, { light: string; dark: string }> = {
  kathmandu: { light: kathmanduLight, dark: kathmanduDark },
  lisbon: { light: lisbonLight, dark: lisbonDark },
  kyoto: { light: kyotoLight, dark: kyotoDark },
}

const SHOWN_DAYS = 3

function useSeen<T extends Element>() {
  const ref = useRef<T>(null)
  const [seen, setSeen] = useState(false)
  useEffect(() => {
    const node = ref.current
    if (!node || typeof IntersectionObserver === "undefined") {
      setSeen(true)
      return
    }
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry?.isIntersecting) {
          setSeen(true)
          observer.disconnect()
        }
      },
      { threshold: 0.4 },
    )
    observer.observe(node)
    return () => observer.disconnect()
  }, [])
  return [ref, seen] as const
}

function DayLine({ day }: { day: GalleryPlan["days"][number] }) {
  const places = day.items.filter((item) => item.place && item.mapped)
  return (
    <HStack as="li" align="baseline" gap="2.5">
      <Box
        flexShrink={0}
        w="6"
        textAlign="center"
        fontFamily="mono"
        fontSize="xs"
        fontWeight="700"
        borderRadius="full"
        bg={dayColor(day.day).color}
        color={dayColor(day.day).text}
        aria-hidden="true"
      >
        {day.day}
      </Box>
      <Text fontSize="sm" lineHeight="1.45">
        <Text as="span" srOnly>
          Day {day.day}:{" "}
        </Text>
        <Text as="span" fontWeight="600">
          {day.theme ?? `Day ${day.day}`}
        </Text>
        {places.length > 0 && (
          <Text as="span" color="fg.muted">
            {" · "}
            {places.map((item, index) => (
              <span key={`${item.place}-${index.toString()}`}>
                {index > 0 && ", "}
                {item.place}
                {item.placeNe && (
                  <Text as="span" fontFamily="devanagari" lang="ne">
                    {" "}
                    ({item.placeNe})
                  </Text>
                )}
              </span>
            ))}
          </Text>
        )}
      </Text>
    </HStack>
  )
}

function PlanCard({ plan }: { plan: GalleryPlan }) {
  const reducedMotion = usePrefersReducedMotion()
  const [ref, seen] = useSeen<HTMLDivElement>()
  const basemap = BASEMAPS[plan.id] ?? { light: "", dark: "" }
  const rest = plan.days.length - SHOWN_DAYS
  const revisions = plan.critic.revisions
  return (
    <Stack
      as="li"
      ref={ref}
      gap="0"
      borderWidth="1px"
      borderRadius="card"
      bg="bg.panel"
      overflow="hidden"
    >
      <RunMap
        map={plan.map}
        light={basemap.light}
        dark={basemap.dark}
        aspectRatio={`${plan.map.width} / ${plan.map.height}`}
        showStops={seen || reducedMotion}
        animate={!reducedMotion}
        label={`Map of ${plan.destination} with ${plan.map.stops.length} stops over ${plan.days.length} days`}
      />
      <Stack gap="3" p="4" flex="1">
        <Stack gap="0.5">
          <Heading as="h3" fontSize="xl" fontWeight="800" letterSpacing="-0.01em">
            {plan.destination}
            {plan.destinationNe && (
              <Text as="span" fontFamily="devanagari" fontWeight="600" color="fg.muted" lang="ne">
                {" "}
                {plan.destinationNe}
              </Text>
            )}
          </Heading>
          <Text fontSize="sm" color="fg.muted">
            {plan.days.length} days · {plan.travelers}{" "}
            {plan.travelers === 1 ? "traveller" : "travellers"} · {plan.pace} pace ·{" "}
            {plan.interests.join(", ")}
          </Text>
        </Stack>
        <Stack as="ol" listStyleType="none" gap="1.5">
          {plan.days.slice(0, SHOWN_DAYS).map((day) => (
            <DayLine key={day.day} day={day} />
          ))}
        </Stack>
        {rest > 0 && (
          <Box as="details" fontSize="sm">
            <Box as="summary" cursor="pointer" color="brand.fg" w="fit-content">
              {rest} more {rest === 1 ? "day" : "days"}
            </Box>
            <Stack as="ol" listStyleType="none" gap="1.5" mt="1.5">
              {plan.days.slice(SHOWN_DAYS).map((day) => (
                <DayLine key={day.day} day={day} />
              ))}
            </Stack>
          </Box>
        )}
        <Stack gap="0.5" mt="auto" pt="2" borderTopWidth="1px" fontSize="sm" color="fg.muted">
          {plan.estimatedTotal !== null && (
            <Text>
              About{" "}
              <Text
                as="span"
                color="fg"
                fontWeight="600"
                style={{ fontVariantNumeric: "tabular-nums" }}
              >
                {formatMoney(plan.estimatedTotal, plan.currency)}
              </Text>{" "}
              for {plan.travelers === 1 ? "one" : plan.travelers}, sample prices in {plan.currency}
            </Text>
          )}
          <Text>
            Planned in{" "}
            <Text
              as="span"
              color="fg"
              fontWeight="600"
              style={{ fontVariantNumeric: "tabular-nums" }}
            >
              {formatElapsed(plan.durationMs)}
            </Text>
            {revisions > 0
              ? `, ${revisions} ${revisions === 1 ? "revision" : "revisions"} after the critic`
              : ", approved on the first review"}
            , {recordedOn(plan.recordedAt)}
          </Text>
        </Stack>
      </Stack>
    </Stack>
  )
}

export function Gallery() {
  return (
    <Section
      id="plans"
      title="Three real plans"
      lead="The sample trips from the demo, planned on the production server. Saved as they came out, thin days included."
    >
      {/* Phones swipe through the plans instead of scrolling past three long cards. */}
      <SimpleGrid
        as="ul"
        listStyleType="none"
        columns={{ md: 2, xl: 3 }}
        gap="4"
        display={{ base: "flex", md: "grid" }}
        // Positioned, so visually hidden text inside the cards scrolls with them.
        position="relative"
        overflowX={{ base: "auto", md: "visible" }}
        scrollSnapType={{ base: "x mandatory", md: "none" }}
        mx={{ base: "-4", md: "0" }}
        px={{ base: "4", md: "0" }}
        pb={{ base: "2", md: "0" }}
        css={{ "& > li": { scrollSnapAlign: "start", flex: { base: "0 0 86%", md: "initial" } } }}
        aria-label="Plans"
      >
        {GALLERY.map((plan) => (
          <PlanCard key={plan.id} plan={plan} />
        ))}
      </SimpleGrid>
    </Section>
  )
}
