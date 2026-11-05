/** `trip.plan` is stored JSON (backend `TripPlan` + sources + review); read it defensively. */
export interface PlanView {
  summary: string
  themes: Record<string, string>
  estimatedTotal: number | null
  breakdown: Array<[string, number]>
  packingTips: string[]
  localTips: string[]
  sources: Array<{ title: string; url: string }>
}

const strings = (value: unknown): string[] =>
  Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : []

export function readPlan(plan: Record<string, unknown> | null | undefined): PlanView | null {
  if (!plan || typeof plan !== "object") return null
  const themes: Record<string, string> = {}
  if (Array.isArray(plan.days)) {
    for (const day of plan.days as Array<Record<string, unknown>>) {
      if (typeof day?.date === "string" && typeof day.theme === "string")
        themes[day.date] = day.theme
    }
  }
  const breakdown =
    plan.budget_breakdown && typeof plan.budget_breakdown === "object"
      ? Object.entries(plan.budget_breakdown as Record<string, unknown>).flatMap(([key, value]) =>
          typeof value === "number" && Number.isFinite(value)
            ? [[key, value] as [string, number]]
            : [],
        )
      : []
  const sources = Array.isArray(plan.sources)
    ? (plan.sources as Array<Record<string, unknown>>).flatMap((source) =>
        typeof source?.url === "string"
          ? [
              {
                url: source.url,
                title: typeof source.title === "string" ? source.title : source.url,
              },
            ]
          : [],
      )
    : []
  return {
    summary: typeof plan.summary === "string" ? plan.summary : "",
    themes,
    estimatedTotal:
      typeof plan.estimated_total === "number" && Number.isFinite(plan.estimated_total)
        ? plan.estimated_total
        : null,
    breakdown,
    packingTips: strings(plan.packing_tips),
    localTips: strings(plan.local_tips),
    sources,
  }
}
