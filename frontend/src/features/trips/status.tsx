import { Badge } from "@chakra-ui/react"
import type { TripStatus } from "@/client/types.gen"

export const TRIP_STATUSES = [
  "draft",
  "planning",
  "planned",
  "booked",
  "completed",
  "cancelled",
] as const satisfies readonly TripStatus[]

const META: Record<TripStatus, { label: string; palette: string }> = {
  draft: { label: "Draft", palette: "gray" },
  planning: { label: "Planning", palette: "brand" },
  planned: { label: "Planned", palette: "sea" },
  booked: { label: "Booked", palette: "green" },
  completed: { label: "Completed", palette: "purple" },
  cancelled: { label: "Cancelled", palette: "red" },
}

export function statusLabel(status: TripStatus): string {
  return META[status].label
}

export function StatusPill({ status }: { status: TripStatus }) {
  const meta = META[status]
  return (
    <Badge colorPalette={meta.palette} variant="subtle" borderRadius="full" px="2.5" size="sm">
      {meta.label}
    </Badge>
  )
}
