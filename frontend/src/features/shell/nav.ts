import type { IconType } from "react-icons"
import { LuMap, LuMessageCircle, LuSettings, LuStickyNote } from "react-icons/lu"

export interface NavItem {
  to: "/trips" | "/assistant" | "/notes" | "/settings"
  label: string
  icon: IconType
}

export const NAV_ITEMS: NavItem[] = [
  { to: "/trips", label: "Trips", icon: LuMap },
  { to: "/assistant", label: "Assistant", icon: LuMessageCircle },
  { to: "/notes", label: "Notes", icon: LuStickyNote },
  { to: "/settings", label: "Settings", icon: LuSettings },
]
