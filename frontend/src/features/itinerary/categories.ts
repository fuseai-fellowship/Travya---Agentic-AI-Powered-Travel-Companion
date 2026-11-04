import type { IconType } from "react-icons"
import { LuBed, LuBus, LuCircleDot, LuLandmark, LuTicket, LuUtensils } from "react-icons/lu"
import type { ItemCategory } from "@/client/types.gen"

export const ITEM_CATEGORIES = [
  "sight",
  "food",
  "activity",
  "transport",
  "lodging",
  "other",
] as const satisfies readonly ItemCategory[]

export const CATEGORY_LABELS: Record<ItemCategory, string> = {
  sight: "Sight",
  food: "Food",
  activity: "Activity",
  transport: "Transport",
  lodging: "Stay",
  other: "Other",
}

export const CATEGORY_ICONS: Record<ItemCategory, IconType> = {
  sight: LuLandmark,
  food: LuUtensils,
  activity: LuTicket,
  transport: LuBus,
  lodging: LuBed,
  other: LuCircleDot,
}
