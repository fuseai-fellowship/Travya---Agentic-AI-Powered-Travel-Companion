import { Link } from "@tanstack/react-router"
import { FaUserAstronaut } from "react-icons/fa"
import { FiLogOut, FiUser } from "react-icons/fi"
import { useState } from "react"

import useAuth from "@/hooks/useAuth"

const UserMenu = () => {
  const { user, logout } = useAuth()
  const [isOpen, setIsOpen] = useState(false)

  const handleLogout = async () => {
    logout()
  }

  return (
    <div className="user-menu">
      <button
        className="user-menu-trigger"
        onClick={() => setIsOpen(!isOpen)}
        data-testid="user-menu"
      >
        <FaUserAstronaut />
        <span>{user?.full_name || "User"}</span>
      </button>

      {isOpen && (
        <div className="user-menu-content">
          <Link to="settings" onClick={() => setIsOpen(false)}>
            <div className="user-menu-item">
              <FiUser />
              <span>My Profile</span>
            </div>
          </Link>

          <div className="user-menu-item" onClick={handleLogout}>
            <FiLogOut />
            <span>Log Out</span>
          </div>
        </div>
      )}
    </div>
  )
}

export default UserMenu
