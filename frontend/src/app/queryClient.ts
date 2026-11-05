import { MutationCache, QueryClient } from "@tanstack/react-query"
import { ApiError } from "@/lib/errors"
import { notifyError } from "@/lib/notify"

declare module "@tanstack/react-query" {
  interface Register {
    mutationMeta: { silent?: boolean; errorTitle?: string }
  }
}

function shouldRetry(failureCount: number, error: unknown): boolean {
  if (error instanceof ApiError && error.status >= 400 && error.status < 500) return false
  if (error instanceof ApiError && error.kind === "demo_limit") return false
  return failureCount < 2
}

export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        retry: shouldRetry,
        refetchOnWindowFocus: false,
      },
      mutations: { retry: false },
    },
    // Every mutation reports its failure once, with the API's problem+json detail.
    mutationCache: new MutationCache({
      onError: (error, _variables, _context, mutation) => {
        if (mutation.meta?.silent) return
        notifyError(error, mutation.meta?.errorTitle)
      },
    }),
  })
}
