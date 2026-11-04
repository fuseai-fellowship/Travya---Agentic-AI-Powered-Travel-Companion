import { Alert, Button, EmptyState, Skeleton, Stack, VStack } from "@chakra-ui/react"
import type { ReactNode } from "react"
import { LuRefreshCw } from "react-icons/lu"
import { errorMessage } from "@/lib/errors"

export function ErrorState({
  error,
  title = "Couldn't load this",
  onRetry,
}: {
  error: unknown
  title?: string
  onRetry?: () => void
}) {
  return (
    <Alert.Root status="error" borderRadius="card" alignItems="flex-start">
      <Alert.Indicator />
      <Alert.Content gap="2">
        <Alert.Title>{title}</Alert.Title>
        <Alert.Description>{errorMessage(error)}</Alert.Description>
        {onRetry && (
          <Button size="sm" variant="outline" alignSelf="flex-start" onClick={onRetry}>
            <LuRefreshCw /> Retry
          </Button>
        )}
      </Alert.Content>
    </Alert.Root>
  )
}

export function Empty({
  icon,
  title,
  description,
  children,
}: {
  icon?: ReactNode
  title: string
  description?: ReactNode
  children?: ReactNode
}) {
  return (
    <EmptyState.Root borderWidth="1px" borderStyle="dashed" borderRadius="card" size="md">
      <EmptyState.Content>
        {icon && <EmptyState.Indicator color="brand.fg">{icon}</EmptyState.Indicator>}
        <VStack textAlign="center" gap="1">
          <EmptyState.Title fontFamily="heading" fontSize="xl">
            {title}
          </EmptyState.Title>
          {description && <EmptyState.Description>{description}</EmptyState.Description>}
        </VStack>
        {children}
      </EmptyState.Content>
    </EmptyState.Root>
  )
}

export function ListSkeleton({ rows = 3, height = "72px" }: { rows?: number; height?: string }) {
  return (
    <Stack gap="3" role="status" aria-busy="true" aria-label="Loading">
      {Array.from({ length: rows }, (_, index) => `row-${index}`).map((key) => (
        <Skeleton key={key} height={height} borderRadius="card" />
      ))}
    </Stack>
  )
}
