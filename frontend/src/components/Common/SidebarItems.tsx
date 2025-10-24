import { useQueryClient } from "@tanstack/react-query"
import { Link as RouterLink } from "@tanstack/react-router"
import { FiBriefcase, FiHome, FiSettings, FiUsers, FiMapPin, FiCalendar, FiMessageCircle, FiPlus } from "react-icons/fi"
import type { IconType } from "react-icons/lib"

import type { UserPublic } from "@/client"

const items = [
  { icon: FiHome, title: "Dashboard", path: "/" },
  { icon: FiMapPin, title: "My Trips", path: "/trips" },
  { icon: FiPlus, title: "Plan Trip", path: "/plan-trip" },
  { icon: FiMessageCircle, title: "AI Chat", path: "/chat" },
  { icon: FiCalendar, title: "Itineraries", path: "/itineraries" },
  { icon: FiBriefcase, title: "Items", path: "/items" },
  { icon: FiSettings, title: "User Settings", path: "/settings" },
]

interface SidebarItemsProps {
  onClose?: () => void
}

interface Item {
  icon: IconType
  title: string
  path: string
}

const SidebarItems = ({ onClose }: SidebarItemsProps) => {
  const queryClient = useQueryClient()
  const currentUser = queryClient.getQueryData<UserPublic>(["currentUser"])

  const finalItems: Item[] = currentUser?.is_superuser
    ? [...items, { icon: FiUsers, title: "Admin", path: "/admin" }]
    : items

  const listItems = finalItems.map(({ icon: IconComponent, title, path }) => (
    <RouterLink key={title} to={path} onClick={onClose} className="sidebar-link">
      <div className="sidebar-item">
        <IconComponent className="sidebar-icon" />
        <span className="sidebar-text">{title}</span>
      </div>
    </RouterLink>
  ))

  return (
    <div className="sidebar-items">
      <div className="sidebar-section-title">Menu</div>
      <div className="sidebar-list">{listItems}</div>
    </div>
  )
}

export default SidebarItems
