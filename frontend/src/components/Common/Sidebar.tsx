import { useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { FaBars } from "react-icons/fa"
import { FiLogOut } from "react-icons/fi"

import type { UserPublic } from "@/client"
import useAuth from "@/hooks/useAuth"
import SidebarItems from "./SidebarItems"

const Sidebar = () => {
  const queryClient = useQueryClient()
  const currentUser = queryClient.getQueryData<UserPublic>(["currentUser"])
  const { logout } = useAuth()
  const [open, setOpen] = useState(false)

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        className="mobile-menu-btn"
        onClick={() => setOpen(!open)}
        aria-label="Open Menu"
      >
        <FaBars />
      </button>

      {/* Mobile Drawer */}
      {open && (
        <div className="mobile-drawer">
          <div className="mobile-drawer-content">
            <button
              className="mobile-drawer-close"
              onClick={() => setOpen(false)}
            >
              ×
            </button>
            <div className="mobile-drawer-body">
              <SidebarItems onClose={() => setOpen(false)} />
              <button
                className="logout-btn"
                onClick={() => {
                  logout()
                }}
              >
                <FiLogOut />
                Log Out
              </button>
            </div>
            {currentUser?.email && (
              <div className="user-info">
                Logged in as: {currentUser.email}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Desktop Sidebar */}
      <div className="desktop-sidebar">
        <div className="sidebar-content">
          <SidebarItems />
        </div>
      </div>
    </>
  )
}

export default Sidebar
