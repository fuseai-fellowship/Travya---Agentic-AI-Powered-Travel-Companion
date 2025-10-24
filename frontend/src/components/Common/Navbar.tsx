import { Link } from "@tanstack/react-router"
import { useState } from "react"
import { FaBars } from "react-icons/fa"
import { FiLogOut } from "react-icons/fi"

import Logo from "/assets/images/fastapi-logo.svg"
import UserMenu from "./UserMenu"
import SidebarItems from "./SidebarItems"
import useAuth from "@/hooks/useAuth"

function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const { logout } = useAuth()

  return (
    <>
      <nav className="navbar">
        <div className="navbar-left">
          <button
            className="mobile-menu-btn"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Open Menu"
          >
            <FaBars />
          </button>
          <Link to="/" className="navbar-logo">
            <img src={Logo} alt="Travya Logo" className="navbar-logo-img" />
          </Link>
        </div>
        <div className="navbar-actions">
          <UserMenu />
        </div>
      </nav>

      {/* Mobile Menu Overlay */}
      {mobileMenuOpen && (
        <div className="mobile-drawer">
          <div className="mobile-drawer-content">
            <button
              className="mobile-drawer-close"
              onClick={() => setMobileMenuOpen(false)}
            >
              ×
            </button>
            <div className="mobile-drawer-body">
              <SidebarItems onClose={() => setMobileMenuOpen(false)} />
              <button
                className="logout-btn"
                onClick={() => {
                  logout()
                  setMobileMenuOpen(false)
                }}
              >
                <FiLogOut />
                Log Out
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default Navbar
