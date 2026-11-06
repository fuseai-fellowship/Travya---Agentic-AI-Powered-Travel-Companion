import { QueryClientProvider } from "@tanstack/react-query"
import { renderHook, waitFor } from "@testing-library/react"
import { HttpResponse, http } from "msw"
import type { ReactNode } from "react"
import { useForm } from "react-hook-form"
import { beforeAll, describe, expect, it, vi } from "vitest"
import { createQueryClient } from "@/app/queryClient"
import { setupApiClient } from "@/lib/api"
import * as fixtures from "@/test/fixtures"
import { server } from "@/test/server"
import { emptyFormValues } from "./samples"
import type { TripFormValues } from "./tripSchema"
import { useProfileDefaults } from "./useProfileDefaults"

vi.mock("@/lib/firebase", async () => (await import("@/test/sse")).firebaseMock)

beforeAll(() => setupApiClient())

function wrapper({ children }: { children: ReactNode }) {
  return <QueryClientProvider client={createQueryClient()}>{children}</QueryClientProvider>
}

function useFormWithDefaults(enabled: boolean) {
  const form = useForm<TripFormValues>({ defaultValues: emptyFormValues() })
  useProfileDefaults(form, enabled)
  return form
}

describe("useProfileDefaults", () => {
  it("fills origin and currency from the profile", async () => {
    server.use(
      http.get("http://localhost:8000/api/v1/me", () =>
        HttpResponse.json({ ...fixtures.me, home_city: "Pokhara", currency: "EUR" }),
      ),
    )
    const { result } = renderHook(() => useFormWithDefaults(true), { wrapper })
    await waitFor(() => expect(result.current.getValues("origin")).toBe("Pokhara"))
    expect(result.current.getValues("currency")).toBe("EUR")
  })

  it("leaves samples alone", () => {
    const { result } = renderHook(() => useFormWithDefaults(false), { wrapper })
    expect(result.current.getValues("origin")).toBe("")
    expect(result.current.getValues("currency")).toBe("USD")
  })
})
