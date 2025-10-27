import { useTheme } from "next-themes"
import { FiMonitor, FiMoon, FiSun } from "react-icons/fi"

const Appearance = () => {
  const { theme, setTheme } = useTheme()

  const themes = [
    { value: "system", label: "System", icon: FiMonitor },
    { value: "light", label: "Light", icon: FiSun },
    { value: "dark", label: "Dark", icon: FiMoon },
  ]

  return (
    <div className="appearance-settings">
      <div className="appearance-header">
        <h2 className="appearance-title">Theme Preferences</h2>
        <p className="appearance-subtitle">Choose how Travya looks to you</p>
      </div>

      <div className="appearance-options">
        {themes.map(({ value, label, icon: Icon }) => (
          <button
            key={value}
            className={`appearance-option ${theme === value ? 'active' : ''}`}
            onClick={() => setTheme(value)}
          >
            <div className="appearance-icon">
              <Icon size={24} />
            </div>
            <div className="appearance-info">
              <div className="appearance-label">{label}</div>
              <div className="appearance-description">
                {value === 'system' && 'Automatically switch between light and dark themes'}
                {value === 'light' && 'Optimized for brightness and clarity'}
                {value === 'dark' && 'Easier on the eyes in low light'}
              </div>
            </div>
            {theme === value && (
              <div className="appearance-check">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M10 18a8 8 0 1 0 0-16 8 8 0 0 0 0 16zM8.707 7.293a1 1 0 0 0-1.414 1.414l2.293 2.293a1 1 0 0 0 1.414 0l4.293-4.293a1 1 0 1 0-1.414-1.414L10 9.586 8.707 8.293z"/>
                </svg>
              </div>
            )}
          </button>
        ))}
      </div>

      <style>{`
        .appearance-settings {
          width: 100%;
        }

        .appearance-header {
          margin-bottom: 32px;
        }

        .appearance-title {
          font-size: 24px;
          font-weight: 600;
          color: #ffffff;
          margin: 0 0 8px 0;
        }

        .appearance-subtitle {
          font-size: 15px;
          color: #86868b;
          margin: 0;
        }

        .appearance-options {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .appearance-option {
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 20px;
          background: rgba(255, 255, 255, 0.05);
          border: 2px solid rgba(255, 255, 255, 0.08);
          border-radius: 12px;
          cursor: pointer;
          transition: all 0.2s ease;
          text-align: left;
        }

        .appearance-option:hover {
          background: rgba(255, 255, 255, 0.08);
          border-color: rgba(255, 255, 255, 0.15);
        }

        .appearance-option.active {
          background: rgba(0, 122, 255, 0.15);
          border-color: #007aff;
        }

        .appearance-icon {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 48px;
          height: 48px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 10px;
          color: #ffffff;
        }

        .appearance-option.active .appearance-icon {
          background: rgba(0, 122, 255, 0.3);
          color: #007aff;
        }

        .appearance-info {
          flex: 1;
        }

        .appearance-label {
          font-size: 16px;
          font-weight: 500;
          color: #ffffff;
          margin-bottom: 4px;
        }

        .appearance-description {
          font-size: 14px;
          color: #86868b;
        }

        .appearance-check {
          color: #007aff;
        }
      `}</style>
    </div>
  )
}
export default Appearance
