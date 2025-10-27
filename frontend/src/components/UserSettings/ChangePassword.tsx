import { useMutation } from "@tanstack/react-query"
import { type SubmitHandler, useForm } from "react-hook-form"
import { FiSave } from "react-icons/fi"
import { useState } from "react"

import { type ApiError, type UpdatePassword, UsersService } from "@/client"
import useCustomToast from "@/hooks/useCustomToast"
import { confirmPasswordRules, handleError, passwordRules } from "@/utils"

interface UpdatePasswordForm extends UpdatePassword {
  confirm_password: string
}

const ChangePassword = () => {
  const { showSuccessToast } = useCustomToast()
  const [showCurrentPassword, setShowCurrentPassword] = useState(false)
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  
  const {
    register,
    handleSubmit,
    reset,
    getValues,
    formState: { errors, isValid, isSubmitting },
  } = useForm<UpdatePasswordForm>({
    mode: "onBlur",
    criteriaMode: "all",
  })

  const mutation = useMutation({
    mutationFn: (data: UpdatePassword) =>
      UsersService.updatePasswordMe({ requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Password updated successfully.")
      reset()
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
  })

  const onSubmit: SubmitHandler<UpdatePasswordForm> = async (data) => {
    mutation.mutate(data)
  }

  return (
    <div className="password-form">
      <div className="password-header">
        <h2 className="password-title">Change Password</h2>
        <p className="password-subtitle">Update your password to keep your account secure</p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="password-content">
        <div className="form-group">
          <label className="form-label">Current Password</label>
          <div className="password-input-wrapper">
            <input
              {...register("current_password", passwordRules())}
              type={showCurrentPassword ? "text" : "password"}
              className={`form-input ${errors.current_password ? 'error' : ''}`}
              placeholder="Enter your current password"
            />
            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowCurrentPassword(!showCurrentPassword)}
            >
              {showCurrentPassword ? '👁️' : '🙈'}
            </button>
          </div>
          {errors.current_password && (
            <span className="form-error">{errors.current_password.message}</span>
          )}
        </div>

        <div className="form-group">
          <label className="form-label">New Password</label>
          <div className="password-input-wrapper">
            <input
              {...register("new_password", passwordRules())}
              type={showNewPassword ? "text" : "password"}
              className={`form-input ${errors.new_password ? 'error' : ''}`}
              placeholder="Enter your new password"
            />
            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowNewPassword(!showNewPassword)}
            >
              {showNewPassword ? '👁️' : '🙈'}
            </button>
          </div>
          {errors.new_password && (
            <span className="form-error">{errors.new_password.message}</span>
          )}
        </div>

        <div className="form-group">
          <label className="form-label">Confirm New Password</label>
          <div className="password-input-wrapper">
            <input
              {...register("confirm_password", confirmPasswordRules(getValues))}
              type={showConfirmPassword ? "text" : "password"}
              className={`form-input ${errors.confirm_password ? 'error' : ''}`}
              placeholder="Confirm your new password"
            />
            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
            >
              {showConfirmPassword ? '👁️' : '🙈'}
            </button>
          </div>
          {errors.confirm_password && (
            <span className="form-error">{errors.confirm_password.message}</span>
          )}
        </div>

        <div className="form-actions">
          <button
            type="submit"
            className="btn-primary"
            disabled={!isValid || isSubmitting}
          >
            <FiSave size={18} />
            {isSubmitting ? 'Updating...' : 'Update Password'}
          </button>
        </div>
      </form>

      <style>{`
        .password-form {
          width: 100%;
        }

        .password-header {
          margin-bottom: 32px;
        }

        .password-title {
          font-size: 24px;
          font-weight: 600;
          color: #ffffff;
          margin: 0 0 8px 0;
        }

        .password-subtitle {
          font-size: 15px;
          color: #86868b;
          margin: 0;
        }

        .password-content {
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

        .password-input-wrapper {
          position: relative;
          display: flex;
          align-items: center;
        }

        .form-input {
          width: 100%;
          padding: 14px 16px 14px 16px;
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

        .password-toggle {
          position: absolute;
          right: 16px;
          background: none;
          border: none;
          cursor: pointer;
          font-size: 18px;
          padding: 4px;
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

        .btn-primary {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 24px;
          background: #007aff;
          color: #ffffff;
          border: none;
          border-radius: 10px;
          font-size: 15px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .btn-primary:hover:not(:disabled) {
          background: #0051d5;
          transform: translateY(-1px);
        }

        .btn-primary:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
      `}</style>
    </div>
  )
}
export default ChangePassword
