import { useQueryClient } from "@tanstack/react-query"
import { Link as RouterLink, useRouter } from "@tanstack/react-router"
import { FiHome, FiSettings, FiUsers, FiMapPin, FiCalendar, FiMessageCircle, FiPlus, FiFileText } from "react-icons/fi"
import type { IconType } from "react-icons/lib"

import type { UserPublic } from "@/client"
import { useSidebar } from "@/contexts/SidebarContext"

const items = [
  { icon: FiHome, title: "Dashboard", path: "/" },
  { icon: FiMapPin, title: "My Trips", path: "/trips" },
  { icon: FiPlus, title: "Plan Trip", path: "/plan-trip" },
  { icon: FiMessageCircle, title: "AI Chat", path: "/chat" },
  { icon: FiCalendar, title: "Itineraries", path: "/itineraries" },
  { icon: FiFileText, title: "Travel Notes", path: "/items" },
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
  const { isCollapsed } = useSidebar()
  const router = useRouter()

  const finalItems: Item[] = currentUser?.is_superuser
    ? [...items, { icon: FiUsers, title: "Admin", path: "/admin" }]
    : items

  const listItems = finalItems.map(({ icon: IconComponent, title, path }) => {
    const isActive = router.state.location.pathname === path
    return (
      <RouterLink 
        key={title} 
        to={path} 
        onClick={onClose} 
        className="sidebar-link"
        data-active={isActive}
      >
        <div className="sidebar-item">
          <IconComponent className="sidebar-icon" />
          {!isCollapsed && <span className="sidebar-text">{title}</span>}
        </div>
      </RouterLink>
    )
  })

  return (
    <div className="sidebar-items">
      {!isCollapsed && <div className="sidebar-section-title">Menu</div>}
      <div className="sidebar-list">{listItems}</div>
    </div>
  )
}

export default SidebarItems
