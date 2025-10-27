import { Outlet, createFileRoute, redirect } from "@tanstack/react-router"

import Navbar from "@/components/Common/Navbar"
import Sidebar from "@/components/Common/Sidebar"
import { AuthProvider } from "@/contexts/AuthContext"
import { TravelProvider } from "@/contexts/TravelContext"
import { SidebarProvider, useSidebar } from "@/contexts/SidebarContext"

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

function LayoutContent() {
  const { isCollapsed } = useSidebar()
  
  return (
    <div className="layout-container">
      <Navbar />
      <div className="layout-content">
        <Sidebar />
        <div 
          className="layout-main"
          style={{
            marginLeft: isCollapsed ? '56px' : '280px'
          }}
        >
          <Outlet />
        </div>
      </div>
    </div>
  )
}

function Layout() {
  return (
    <AuthProvider>
      <TravelProvider>
        <SidebarProvider>
          <LayoutContent />
        </SidebarProvider>
      </TravelProvider>
    </AuthProvider>
  )
}

export default Layout
