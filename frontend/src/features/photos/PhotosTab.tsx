import { Box, Button, HStack, Image, Link, Stack, Text } from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { LuImage, LuRefreshCw } from "react-icons/lu"
import {
  tripsListPhotosOptions,
  tripsListPhotosQueryKey,
  tripsRefreshPhotosMutation,
} from "@/client/@tanstack/react-query.gen"
import { Empty, ErrorState, ListSkeleton } from "@/components/States"

const SOURCE_NAMES: Record<string, string> = {
  unsplash: "Unsplash",
  wikimedia: "Wikimedia Commons",
  picsum: "Lorem Picsum",
}

export function PhotosTab({ tripId }: { tripId: string }) {
  const queryClient = useQueryClient()
  const options = { path: { trip_id: tripId } }
  const query = useQuery(tripsListPhotosOptions(options))
  const refresh = useMutation({
    ...tripsRefreshPhotosMutation(),
    meta: { errorTitle: "Couldn't refresh photos" },
    onSuccess: (photos) => queryClient.setQueryData(tripsListPhotosQueryKey(options), photos),
  })

  if (query.isPending) return <ListSkeleton rows={2} height="180px" />
  if (query.isError)
    return (
      <ErrorState
        error={query.error}
        title="Couldn't load photos"
        onRetry={() => query.refetch()}
      />
    )

  const refreshButton = (
    <Button
      size="sm"
      variant="outline"
      loading={refresh.isPending}
      onClick={() => refresh.mutate(options)}
    >
      <LuRefreshCw /> {query.data.length ? "Refresh photos" : "Find photos"}
    </Button>
  )

  if (!query.data.length) {
    return (
      <Empty
        icon={<LuImage />}
        title="No photos yet"
        description="Find openly licensed photos of the places on this trip."
      >
        {refreshButton}
      </Empty>
    )
  }

  return (
    <Stack gap="3">
      <HStack justify="space-between">
        <Text fontSize="sm" color="fg.muted">
          Openly licensed photos, credited to their authors.
        </Text>
        {refreshButton}
      </HStack>
      <Box
        as="ul"
        listStyleType="none"
        css={{ columnCount: { base: 1, sm: 2 }, columnGap: "12px" }}
      >
        {query.data.map((photo) => (
          <Box as="li" key={photo.id} mb="3" css={{ breakInside: "avoid" }}>
            <Box as="figure" borderRadius="card" overflow="hidden" borderWidth="1px" bg="bg.panel">
              <Image
                src={photo.thumb_url || photo.url}
                alt={photo.alt || photo.place_name}
                width={photo.width}
                height={photo.height}
                loading="lazy"
                w="full"
                h="auto"
              />
              <Box as="figcaption" px="3" py="2" fontSize="xs" color="fg.muted">
                <Text fontWeight="500" color="fg">
                  {photo.place_name}
                </Text>
                Photo by{" "}
                {photo.author_url ? (
                  <Link
                    href={photo.author_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    color="fg.muted"
                    textDecoration="underline"
                  >
                    {photo.author_name}
                  </Link>
                ) : (
                  photo.author_name
                )}{" "}
                on{" "}
                <Link
                  href={photo.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  color="fg.muted"
                  textDecoration="underline"
                >
                  {SOURCE_NAMES[photo.source] ?? photo.source}
                </Link>
              </Box>
            </Box>
          </Box>
        ))}
      </Box>
    </Stack>
  )
}
