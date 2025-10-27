import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { type SubmitHandler, useForm } from "react-hook-form"
import { FiEdit2, FiSave, FiX } from "react-icons/fi"

import {
  type ApiError,
  type UserPublic,
  type UserUpdateMe,
  UsersService,
} from "@/client"
import useAuth from "@/hooks/useAuth"
import useCustomToast from "@/hooks/useCustomToast"
import { emailPattern, handleError } from "@/utils"

const UserInformation = () => {
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()
  const [editMode, setEditMode] = useState(false)
  const { user: currentUser } = useAuth()
  const {
    register,
    handleSubmit,
    reset,
    getValues,
    formState: { isSubmitting, errors, isDirty },
  } = useForm<UserPublic>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      full_name: currentUser?.full_name,
      email: currentUser?.email,
    },
  })

  const toggleEditMode = () => {
    setEditMode(!editMode)
  }

  const mutation = useMutation({
    mutationFn: (data: UserUpdateMe) =>
      UsersService.updateUserMe({ requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Profile updated successfully.")
      setEditMode(false)
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries()
    },
  })

  const onSubmit: SubmitHandler<UserUpdateMe> = async (data) => {
    mutation.mutate(data)
  }

  const onCancel = () => {
    reset()
    toggleEditMode()
  }

  return (
    <div className="user-info-form">
      <div className="form-header">
        <h2 className="form-title">Profile Information</h2>
        {!editMode && (
          <button 
            className="edit-button"
            onClick={toggleEditMode}
            type="button"
          >
            <FiEdit2 size={18} />
            Edit
          </button>
        )}
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="form-content">
        <div className="form-group">
          <label className="form-label">Full Name</label>
          {editMode ? (
            <>
              <input
                {...register("full_name", { maxLength: 30 })}
                type="text"
                className={`form-input ${errors.full_name ? 'error' : ''}`}
                placeholder="Enter your full name"
              />
              {errors.full_name && (
                <span className="form-error">{errors.full_name.message}</span>
              )}
            </>
          ) : (
            <div className="form-field-display">
              {currentUser?.full_name || "Not set"}
            </div>
          )}
        </div>

        <div className="form-group">
          <label className="form-label">Email Address</label>
          {editMode ? (
            <>
              <input
                {...register("email", {
                  required: "Email is required",
                  pattern: emailPattern,
                })}
                type="email"
                className={`form-input ${errors.email ? 'error' : ''}`}
                placeholder="Enter your email"
              />
              {errors.email && (
                <span className="form-error">{errors.email.message}</span>
              )}
            </>
          ) : (
            <div className="form-field-display">
              {currentUser?.email}
            </div>
          )}
        </div>

        {editMode && (
          <div className="form-actions">
            <button
              type="submit"
              className="btn-primary"
              disabled={!isDirty || !getValues("email") || isSubmitting}
            >
              <FiSave size={18} />
              {isSubmitting ? 'Saving...' : 'Save Changes'}
            </button>
            <button
              type="button"
              className="btn-secondary"
              onClick={onCancel}
              disabled={isSubmitting}
            >
              <FiX size={18} />
              Cancel
            </button>
          </div>
        )}
      </form>

      <style>{`
        .user-info-form {
          width: 100%;
        }

        .form-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 32px;
        }

        .form-title {
          font-size: 24px;
          font-weight: 600;
          color: #ffffff;
          margin: 0;
        }

        .edit-button {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 20px;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 8px;
          color: #ffffff;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .edit-button:hover {
          background: rgba(255, 255, 255, 0.1);
          border-color: rgba(255, 255, 255, 0.2);
        }

        .form-content {
          display: flex;
          flex-direction: column;
          gap: 24px;
        }

        .form-group {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .form-label {
          font-size: 13px;
          font-weight: 500;
          color: #86868b;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .form-input {
          width: 100%;
          padding: 14px 16px;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 10px;
          color: #ffffff;
          font-size: 16px;
          font-weight: 400;
          transition: all 0.2s ease;
          outline: none;
        }

        .form-input:focus {
          background: rgba(255, 255, 255, 0.08);
          border-color: #007aff;
          box-shadow: 0 0 0 4px rgba(0, 122, 255, 0.1);
        }

        .form-input.error {
          border-color: #ff3b30;
        }

        .form-input::placeholder {
          color: #86868b;
        }

        .form-field-display {
          padding: 14px 16px;
          color: #ffffff;
          font-size: 16px;
          font-weight: 400;
          background: rgba(255, 255, 255, 0.02);
          border-radius: 10px;
        }

        .form-error {
          font-size: 13px;
          color: #ff3b30;
          margin-top: 4px;
        }

        .form-actions {
          display: flex;
          gap: 12px;
          margin-top: 8px;
        }

        .btn-primary, .btn-secondary {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 24px;
          border: none;
          border-radius: 10px;
          font-size: 15px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .btn-primary {
          background: #007aff;
          color: #ffffff;
        }

        .btn-primary:hover:not(:disabled) {
          background: #0051d5;
          transform: translateY(-1px);
        }

        .btn-primary:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .btn-secondary {
          background: rgba(255, 255, 255, 0.05);
          color: #ffffff;
        }

        .btn-secondary:hover:not(:disabled) {
          background: rgba(255, 255, 255, 0.1);
        }

        .btn-secondary:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
      `}</style>
    </div>
  )
}

export default UserInformation
