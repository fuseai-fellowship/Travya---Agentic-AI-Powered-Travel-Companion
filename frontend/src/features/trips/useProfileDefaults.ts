import { useQuery } from "@tanstack/react-query"
import { useEffect } from "react"
import type { UseFormReturn } from "react-hook-form"
import { accountReadMeOptions } from "@/client/@tanstack/react-query.gen"
import type { TripFormValues } from "./tripSchema"

/**
 * A blank trip starts from the profile's home city (as the origin) and currency, unless the
 * traveller already changed those fields. Samples keep their own values (`enabled` false).
 * Review finding L17: both profile fields were stored but never used.
 */
export function useProfileDefaults(form: UseFormReturn<TripFormValues>, enabled: boolean) {
  const me = useQuery({ ...accountReadMeOptions(), enabled })
  useEffect(() => {
    if (!enabled || !me.data) return
    const { home_city: homeCity, currency } = me.data
    if (homeCity && !form.getFieldState("origin").isDirty && !form.getValues("origin"))
      form.setValue("origin", homeCity)
    if (currency && !form.getFieldState("currency").isDirty) form.setValue("currency", currency)
  }, [me.data, enabled, form])
}
