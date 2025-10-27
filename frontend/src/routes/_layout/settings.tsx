import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"
import { 
  FiUser, 
  FiLock, 
  FiAlertTriangle 
} from "react-icons/fi"

import ChangePassword from "@/components/UserSettings/ChangePassword"
import DeleteAccount from "@/components/UserSettings/DeleteAccount"
import UserInformation from "@/components/UserSettings/UserInformation"
import useAuth from "@/hooks/useAuth"

const tabsConfig = [
  { 
    value: "my-profile", 
    title: "My Profile", 
    icon: FiUser,
    component: UserInformation 
  },
  { 
    value: "password", 
    title: "Password", 
    icon: FiLock,
    component: ChangePassword 
  },
  { 
    value: "danger-zone", 
    title: "Danger Zone", 
    icon: FiAlertTriangle,
    component: DeleteAccount 
  },
]

export const Route = createFileRoute("/_layout/settings")({
  component: UserSettings,
})

function UserSettings() {
  const { user: currentUser } = useAuth()
  const [activeTab, setActiveTab] = useState("my-profile")
  
  const finalTabs = currentUser?.is_superuser
    ? tabsConfig.slice(0, 2)
    : tabsConfig

  if (!currentUser) {
    return null
  }

  const activeComponent = finalTabs.find(tab => tab.value === activeTab)?.component

  return (
    <div className="settings-page">
      <div className="settings-container">
        <div className="settings-header">
          <h1 className="settings-title">Settings</h1>
          <p className="settings-subtitle">Manage your account and preferences</p>
        </div>

        <div className="settings-layout">
          <div className="settings-sidebar">
            <nav className="settings-nav">
              {finalTabs.map((tab) => {
                const Icon = tab.icon
                const isActive = activeTab === tab.value
                return (
                  <button
                    key={tab.value}
                    className={`settings-nav-item ${isActive ? 'active' : ''}`}
                    onClick={() => setActiveTab(tab.value)}
                  >
                    <Icon size={20} />
                    <span>{tab.title}</span>
                  </button>
                )
              })}
            </nav>
          </div>

          <div className="settings-content">
            <div className="settings-content-wrapper">
              {activeComponent && (() => {
                const Component = activeComponent
                return <Component />
              })()}
            </div>
          </div>
        </div>
      </div>

      <style>{`
        .settings-page {
          width: 100%;
          min-height: calc(100vh - 60px);
          background: linear-gradient(to bottom, #1a1a1a 0%, #0a0a0a 100%);
          padding: 60px 40px 40px;
        }

        .settings-container {
          max-width: 1200px;
          margin: 0 auto;
        }

        .settings-header {
          margin-bottom: 40px;
          padding-bottom: 20px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }

        .settings-title {
          font-size: 36px;
          font-weight: 600;
          color: #ffffff;
          margin-bottom: 8px;
          letter-spacing: -0.5px;
        }

        .settings-subtitle {
          font-size: 17px;
          color: #86868b;
          font-weight: 400;
        }

        .settings-layout {
          display: grid;
          grid-template-columns: 240px 1fr;
          gap: 40px;
        }

        .settings-sidebar {
          position: sticky;
          top: 80px;
          height: fit-content;
        }

        .settings-nav {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .settings-nav-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px 16px;
          border-radius: 10px;
          background: transparent;
          border: none;
          color: #86868b;
          font-size: 15px;
          font-weight: 400;
          cursor: pointer;
          transition: all 0.2s ease;
          text-align: left;
        }

        .settings-nav-item:hover {
          background: rgba(255, 255, 255, 0.05);
          color: #ffffff;
        }

        .settings-nav-item.active {
          background: rgba(0, 122, 255, 0.15);
          color: #007aff;
        }

        .settings-nav-item.active span {
          font-weight: 500;
        }

        .settings-content {
          min-height: 500px;
        }

        .settings-content-wrapper {
          background: rgba(255, 255, 255, 0.03);
          backdrop-filter: blur(20px);
          border-radius: 16px;
          padding: 40px;
          border: 1px solid rgba(255, 255, 255, 0.08);
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }

        @media (max-width: 968px) {
          .settings-layout {
            grid-template-columns: 1fr;
          }

          .settings-sidebar {
            position: static;
          }

          .settings-nav {
            flex-direction: row;
            overflow-x: auto;
            padding-bottom: 8px;
          }

          .settings-nav-item {
            white-space: nowrap;
          }

          .settings-page {
            padding: 60px 24px 24px;
          }

          .settings-content-wrapper {
            padding: 24px;
          }
        }
      `}</style>
    </div>
  )
}
