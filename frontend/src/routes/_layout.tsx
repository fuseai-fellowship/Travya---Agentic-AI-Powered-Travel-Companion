import { Outlet, createFileRoute, redirect } from "@tanstack/react-router"

import Navbar from "@/components/Common/Navbar"
import Sidebar from "@/components/Common/Sidebar"
import { AuthProvider } from "@/contexts/AuthContext"
import { TravelProvider } from "@/contexts/TravelContext"

const isLoggedIn = () => {
  return localStorage.getItem("access_token") !== null
}

export const Route = createFileRoute("/_layout")({
  component: Layout,
  beforeLoad: async () => {
    if (!isLoggedIn()) {
      throw redirect({
        to: "/login",
      })
    }
  },
})

function Layout() {
  return (
    <AuthProvider>
      <TravelProvider>
        <div className="layout-container">
          <Navbar />
          <div className="layout-content">
            <Sidebar />
            <div className="layout-main">
              <Outlet />
            </div>
          </div>
        </div>
      </TravelProvider>
    </AuthProvider>
  )
}

export default Layout
