import {
  Button,
  Container,
  Heading,
  HStack,
  Input,
  InputGroup,
  Stack,
  Text,
  Wrap,
} from "@chakra-ui/react"
import { keepPreviousData, useQuery } from "@tanstack/react-query"
import { getRouteApi, Link } from "@tanstack/react-router"
import { useEffect, useState } from "react"
import { LuCompass, LuPlus, LuSearch } from "react-icons/lu"
import { tripsListTripsOptions } from "@/client/@tanstack/react-query.gen"
import type { TripStatus } from "@/client/types.gen"
import { Empty, ErrorState, ListSkeleton } from "@/components/States"
import { useDebouncedValue, useDocumentTitle } from "@/lib/hooks"
import { SampleTrips } from "./SampleTrips"
import { statusLabel, TRIP_STATUSES } from "./status"
import { TripRow } from "./TripRow"

const route = getRouteApi("/_app/trips/")
const PAGE_SIZE = 20

export function TripsPage() {
  useDocumentTitle("Your trips")
  const search = route.useSearch()
  const navigate = route.useNavigate()
  const page = search.page ?? 1
  const [text, setText] = useState(search.q ?? "")
  const debounced = useDebouncedValue(text.trim(), 300)

  useEffect(() => {
    if ((search.q ?? "") !== debounced) {
      void navigate({
        search: (prev) => ({ ...prev, q: debounced || undefined, page: undefined }),
        replace: true,
      })
    }
  }, [debounced, search.q, navigate])

  const query = useQuery({
    ...tripsListTripsOptions({
      query: {
        q: search.q || undefined,
        status: search.status,
        limit: PAGE_SIZE,
        offset: (page - 1) * PAGE_SIZE,
      },
    }),
    placeholderData: keepPreviousData,
  })

  const filtered = Boolean(search.q || search.status)
  const setStatus = (status: TripStatus | undefined) =>
    navigate({ search: (prev) => ({ ...prev, status, page: undefined }) })

  return (
    <Container maxW="5xl" py={{ base: "6", md: "10" }} px={{ base: "4", md: "8" }}>
      <Stack gap="6">
        <HStack justify="space-between" align="end" gap="4" flexWrap="wrap">
          <Stack gap="1">
            <Heading as="h1" fontFamily="heading" size="3xl" fontWeight="600">
              Your trips
            </Heading>
            <Text color="fg.muted">
              Plan, re-plan and keep everything about a trip in one place.
            </Text>
          </Stack>
          <Button asChild colorPalette="brand">
            <Link to="/trips/new">
              <LuPlus /> New trip
            </Link>
          </Button>
        </HStack>

        <Stack gap="3">
          <InputGroup startElement={<LuSearch />} maxW={{ md: "sm" }}>
            <Input
              type="search"
              aria-label="Search trips"
              placeholder="Search by destination or title"
              value={text}
              maxLength={100}
              onChange={(event) => setText(event.target.value)}
            />
          </InputGroup>
          <Wrap gap="2" role="group" aria-label="Filter by status">
            <Button
              size="sm"
              borderRadius="full"
              variant={search.status ? "outline" : "solid"}
              aria-pressed={!search.status}
              onClick={() => setStatus(undefined)}
            >
              All
            </Button>
            {TRIP_STATUSES.map((status) => (
              <Button
                key={status}
                size="sm"
                borderRadius="full"
                variant={search.status === status ? "solid" : "outline"}
                aria-pressed={search.status === status}
                onClick={() => setStatus(status)}
              >
                {statusLabel(status)}
              </Button>
            ))}
          </Wrap>
        </Stack>

        {query.isPending ? (
          <ListSkeleton rows={4} height="104px" />
        ) : query.isError ? (
          <ErrorState
            error={query.error}
            title="Couldn't load your trips"
            onRetry={() => query.refetch()}
          />
        ) : query.data.items.length === 0 ? (
          filtered ? (
            <Empty
              icon={<LuSearch />}
              title="No trips match"
              description="Try another search or status."
            >
              <Button
                variant="outline"
                onClick={() => {
                  setText("")
                  void navigate({ search: {} })
                }}
              >
                Clear filters
              </Button>
            </Empty>
          ) : (
            <Empty
              icon={<LuCompass />}
              title="Plan your first trip"
              description="Pick a sample to watch the agents plan it, or start from scratch."
            >
              <SampleTrips />
              <Button asChild variant="outline">
                <Link to="/trips/new">Start from scratch</Link>
              </Button>
            </Empty>
          )
        ) : (
          <Stack gap="4" opacity={query.isPlaceholderData ? 0.6 : 1} transition="opacity 150ms">
            <Stack as="ul" gap="3" listStyleType="none" aria-label="Trips">
              {query.data.items.map((trip) => (
                <TripRow key={trip.id} trip={trip} />
              ))}
            </Stack>
            <Pagination
              page={page}
              total={query.data.total}
              onPage={(next) =>
                navigate({ search: (prev) => ({ ...prev, page: next > 1 ? next : undefined }) })
              }
            />
          </Stack>
        )}
      </Stack>
    </Container>
  )
}

function Pagination({
  page,
  total,
  onPage,
}: {
  page: number
  total: number
  onPage: (page: number) => void
}) {
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE))
  if (pages <= 1) return null
  const first = (page - 1) * PAGE_SIZE + 1
  const last = Math.min(total, page * PAGE_SIZE)
  return (
    <HStack as="nav" aria-label="Pagination" justify="space-between">
      <Text fontSize="sm" color="fg.muted">
        {first}–{last} of {total}
      </Text>
      <HStack>
        <Button size="sm" variant="outline" disabled={page <= 1} onClick={() => onPage(page - 1)}>
          Previous
        </Button>
        <Button
          size="sm"
          variant="outline"
          disabled={page >= pages}
          onClick={() => onPage(page + 1)}
        >
          Next
        </Button>
      </HStack>
    </HStack>
  )
}
