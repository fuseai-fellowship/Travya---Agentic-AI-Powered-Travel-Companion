import { FiAlertTriangle } from "react-icons/fi"

import DeleteConfirmation from "./DeleteConfirmation"

const DeleteAccount = () => {
  return (
    <div className="delete-account">
      <div className="delete-header">
        <div className="delete-icon-wrapper">
          <FiAlertTriangle className="delete-icon" />
        </div>
        <div>
          <h2 className="delete-title">Delete Account</h2>
          <p className="delete-subtitle">
            This action cannot be undone
          </p>
        </div>
      </div>

      <div className="delete-content">
        <p className="delete-description">
          Once you delete your account, there is no going back. All of your data, 
          trips, conversations, and settings will be permanently removed from our servers.
        </p>

        <div className="delete-warning">
          <strong>Warning:</strong> This will delete all of your:
          <ul>
            <li>Trips and itineraries</li>
            <li>Travel conversations with AI</li>
            <li>Personal information and settings</li>
            <li>Account credentials</li>
          </ul>
        </div>

        <DeleteConfirmation />
      </div>

      <style>{`
        .delete-account {
          width: 100%;
        }

        .delete-header {
          display: flex;
          align-items: center;
          gap: 20px;
          margin-bottom: 32px;
          padding-bottom: 24px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }

        .delete-icon-wrapper {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 64px;
          height: 64px;
          background: rgba(255, 59, 48, 0.15);
          border-radius: 16px;
        }

        .delete-icon {
          color: #ff3b30;
          width: 32px;
          height: 32px;
        }

        .delete-title {
          font-size: 24px;
          font-weight: 600;
          color: #ff3b30;
          margin: 0 0 4px 0;
        }

        .delete-subtitle {
          font-size: 15px;
          color: #86868b;
          margin: 0;
        }

        .delete-content {
          display: flex;
          flex-direction: column;
          gap: 24px;
        }

        .delete-description {
          font-size: 16px;
          color: #ffffff;
          line-height: 1.6;
          margin: 0;
        }

        .delete-warning {
          padding: 20px;
          background: rgba(255, 59, 48, 0.1);
          border: 1px solid rgba(255, 59, 48, 0.2);
          border-radius: 12px;
          font-size: 15px;
          color: #ff3b30;
          line-height: 1.6;
        }

        .delete-warning strong {
          display: block;
          margin-bottom: 12px;
          font-weight: 600;
        }

        .delete-warning ul {
          margin: 8px 0 0 20px;
          list-style: disc;
        }

        .delete-warning li {
          margin-bottom: 4px;
        }
      `}</style>
    </div>
  )
}
export default DeleteAccount
