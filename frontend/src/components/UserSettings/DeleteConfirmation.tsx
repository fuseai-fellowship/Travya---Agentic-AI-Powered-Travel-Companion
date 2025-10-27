import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { FiX } from "react-icons/fi"

import { type ApiError, UsersService } from "@/client"
import useAuth from "@/hooks/useAuth"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

const DeleteConfirmation = () => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()
  const { logout } = useAuth()
  const [isSubmitting, setIsSubmitting] = useState(false)

  const mutation = useMutation({
    mutationFn: () => UsersService.deleteUserMe(),
    onSuccess: () => {
      showSuccessToast("Your account has been successfully deleted")
      setIsOpen(false)
      logout()
    },
    onError: (err: ApiError) => {
      handleError(err)
      setIsSubmitting(false)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["currentUser"] })
      setIsSubmitting(false)
    },
  })

  const onSubmit = async () => {
    setIsSubmitting(true)
    mutation.mutate()
  }

  return (
    <>
      <button 
        className="delete-account-button"
        onClick={() => setIsOpen(true)}
      >
        Delete My Account
      </button>

      {isOpen && (
        <>
          <div className="modal-overlay" onClick={() => !isSubmitting && setIsOpen(false)} />
          <div className="modal-container">
            <div className="modal-header">
              <h3 className="modal-title">Delete Your Account?</h3>
              <button 
                className="modal-close"
                onClick={() => setIsOpen(false)}
                disabled={isSubmitting}
              >
                <FiX size={24} />
              </button>
            </div>

            <div className="modal-body">
              <p className="modal-message">
                This will permanently delete your account and all associated data. 
                This action <strong>cannot be undone</strong>.
              </p>
            </div>

            <div className="modal-footer">
              <button
                className="btn-cancel"
                onClick={() => setIsOpen(false)}
                disabled={isSubmitting}
              >
                Cancel
              </button>
              <button
                className="btn-delete"
                onClick={onSubmit}
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Deleting...' : 'Delete Account'}
              </button>
            </div>
          </div>
        </>
      )}

      <style>{`
        .delete-account-button {
          padding: 14px 28px;
          background: #ff3b30;
          border: none;
          border-radius: 10px;
          color: #ffffff;
          font-size: 15px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .delete-account-button:hover {
          background: #ff1e11;
          transform: translateY(-1px);
        }

        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.7);
          backdrop-filter: blur(10px);
          z-index: 1000;
        }

        .modal-container {
          position: fixed;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: 90%;
          max-width: 480px;
          background: rgba(30, 30, 30, 0.98);
          backdrop-filter: blur(40px);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 20px;
          box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
          z-index: 1001;
        }

        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 24px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .modal-title {
          font-size: 20px;
          font-weight: 600;
          color: #ff3b30;
          margin: 0;
        }

        .modal-close {
          background: none;
          border: none;
          color: #86868b;
          cursor: pointer;
          padding: 4px;
          transition: color 0.2s ease;
        }

        .modal-close:hover:not(:disabled) {
          color: #ffffff;
        }

        .modal-body {
          padding: 24px;
        }

        .modal-message {
          font-size: 15px;
          color: #ffffff;
          line-height: 1.6;
          margin: 0;
        }

        .modal-footer {
          display: flex;
          gap: 12px;
          padding: 24px;
          border-top: 1px solid rgba(255, 255, 255, 0.1);
        }

        .btn-cancel, .btn-delete {
          flex: 1;
          padding: 12px 24px;
          border: none;
          border-radius: 10px;
          font-size: 15px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .btn-cancel {
          background: rgba(255, 255, 255, 0.05);
          color: #ffffff;
        }

        .btn-cancel:hover:not(:disabled) {
          background: rgba(255, 255, 255, 0.1);
        }

        .btn-delete {
          background: #ff3b30;
          color: #ffffff;
        }

        .btn-delete:hover:not(:disabled) {
          background: #ff1e11;
        }

        .btn-cancel:disabled, .btn-delete:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
      `}</style>
    </>
  )
}

export default DeleteConfirmation
