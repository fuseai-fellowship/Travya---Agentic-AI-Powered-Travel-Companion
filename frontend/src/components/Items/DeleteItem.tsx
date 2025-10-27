import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { createPortal } from "react-dom"
import { FiTrash2 } from "react-icons/fi"

import { ItemsService } from "@/client"
import useCustomToast from "@/hooks/useCustomToast"

const DeleteItem = ({ id, onDelete }: { id: string, onDelete?: () => void }) => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const deleteItem = async (id: string) => {
    await ItemsService.deleteItem({ id: id })
  }

  const mutation = useMutation({
    mutationFn: deleteItem,
    onSuccess: () => {
      showSuccessToast("Note deleted successfully")
      setIsOpen(false)
      onDelete?.()
    },
    onError: () => {
      showErrorToast("An error occurred while deleting the note")
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["items"] })
    },
  })

  const handleDelete = async () => {
    mutation.mutate(id)
  }

  return (
    <>
      <button className="delete-btn" onClick={() => setIsOpen(true)}>
        <FiTrash2 size={16} />
      </button>

      {isOpen && createPortal(
        <>
          <div className="modal-overlay" onClick={() => setIsOpen(false)} />
          <div className="modal-container">
            <div className="modal-header">
              <h3 className="modal-title">Delete Note?</h3>
              <p className="modal-message">
                This note will be permanently deleted. This action cannot be undone.
              </p>
            </div>

            <div className="modal-footer">
              <button
                className="btn-cancel"
                onClick={() => setIsOpen(false)}
                disabled={mutation.isPending}
              >
                Cancel
              </button>
              <button
                className="btn-delete"
                onClick={handleDelete}
                disabled={mutation.isPending}
              >
                {mutation.isPending ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </>,
        document.body
      )}

      <style>{`
        .delete-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 32px;
          height: 32px;
          background: rgba(255, 59, 48, 0.2);
          border: none;
          border-radius: 6px;
          color: #ff3b30;
          cursor: pointer;
          transition: all 0.2s ease;
        }
        .delete-btn:hover {
          background: rgba(255, 59, 48, 0.3);
          transform: scale(1.1);
        }
        .modal-overlay {
          position: fixed !important;
          top: 0 !important;
          left: 0 !important;
          right: 0 !important;
          bottom: 0 !important;
          background: rgba(0, 0, 0, 0.7);
          backdrop-filter: blur(10px);
          z-index: 99999 !important;
        }
        .modal-container {
          position: fixed !important;
          top: 50% !important;
          left: 50% !important;
          transform: translate(-50%, -50%) !important;
          width: 90%;
          max-width: 400px;
          background: rgba(30, 30, 30, 0.98);
          backdrop-filter: blur(40px);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 20px;
          box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
          z-index: 100000 !important;
          padding: 24px;
          margin: 0 !important;
        }
        .modal-header {
          margin-bottom: 24px;
        }
        .modal-title {
          font-size: 20px;
          font-weight: 600;
          color: #ff3b30;
          margin: 0 0 12px 0;
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

export default DeleteItem
