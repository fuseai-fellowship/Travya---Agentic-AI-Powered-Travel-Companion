import { Alert, Button, Field, Input, Stack, Text } from "@chakra-ui/react"
import { zodResolver } from "@hookform/resolvers/zod"
import { getRouteApi, Link } from "@tanstack/react-router"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { PasswordInput } from "@/components/PasswordInput"
import { AuthLayout } from "./AuthLayout"
import { completePasswordReset, requestPasswordReset } from "./actions"
import { firebaseErrorCode, firebaseErrorMessage } from "./firebaseErrors"

const route = getRouteApi("/reset-password")

const requestSchema = z.object({ email: z.email("Enter a valid email address") })
const resetSchema = z.object({ password: z.string().min(8, "Use at least 8 characters") })

export function ResetPasswordPage() {
  const { oobCode } = route.useSearch()
  return oobCode ? <NewPasswordForm code={oobCode} /> : <RequestResetForm />
}

function RequestResetForm() {
  const [sentTo, setSentTo] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<z.infer<typeof requestSchema>>({ resolver: zodResolver(requestSchema) })

  const onSubmit = handleSubmit(async ({ email }) => {
    setError(null)
    try {
      await requestPasswordReset(email)
      setSentTo(email)
    } catch (caught) {
      // Never reveal whether an account exists: an unknown email gets the same answer.
      if (firebaseErrorCode(caught) === "auth/user-not-found") setSentTo(email)
      else setError(firebaseErrorMessage(caught))
    }
  })

  return (
    <AuthLayout
      title="Reset your password"
      subtitle="We'll email you a link to choose a new one"
      footer={<Link to="/login">Back to sign in</Link>}
    >
      {sentTo ? (
        <Alert.Root status="success" role="status">
          <Alert.Indicator />
          <Alert.Content>
            <Alert.Title>Check your inbox</Alert.Title>
            <Alert.Description>
              If an account exists for {sentTo}, a reset link is on its way.
            </Alert.Description>
          </Alert.Content>
        </Alert.Root>
      ) : (
        <Stack asChild gap="4">
          <form onSubmit={onSubmit} noValidate>
            {error && (
              <Alert.Root status="error" size="sm">
                <Alert.Indicator />
                <Alert.Title>{error}</Alert.Title>
              </Alert.Root>
            )}
            <Field.Root invalid={!!errors.email}>
              <Field.Label>Email</Field.Label>
              <Input
                type="email"
                autoComplete="email"
                placeholder="Enter your email"
                size="lg"
                {...register("email")}
              />
              <Field.ErrorText>{errors.email?.message}</Field.ErrorText>
            </Field.Root>
            <Button type="submit" size="lg" colorPalette="brand" loading={isSubmitting}>
              Send reset link
            </Button>
          </form>
        </Stack>
      )}
    </AuthLayout>
  )
}

function NewPasswordForm({ code }: { code: string }) {
  const [done, setDone] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<z.infer<typeof resetSchema>>({ resolver: zodResolver(resetSchema) })

  const onSubmit = handleSubmit(async ({ password }) => {
    setError(null)
    try {
      await completePasswordReset(code, password)
      setDone(true)
    } catch (caught) {
      setError(firebaseErrorMessage(caught))
    }
  })

  return (
    <AuthLayout title="Choose a new password" subtitle="Use at least 8 characters">
      {done ? (
        <Stack gap="4">
          <Text role="status">Your password was changed.</Text>
          <Button asChild colorPalette="brand" size="lg">
            <Link to="/login">Sign in</Link>
          </Button>
        </Stack>
      ) : (
        <Stack asChild gap="4">
          <form onSubmit={onSubmit} noValidate>
            {error && (
              <Alert.Root status="error" size="sm">
                <Alert.Indicator />
                <Alert.Title>{error}</Alert.Title>
              </Alert.Root>
            )}
            <Field.Root invalid={!!errors.password}>
              <Field.Label>New password</Field.Label>
              <PasswordInput autoComplete="new-password" size="lg" {...register("password")} />
              <Field.ErrorText>{errors.password?.message}</Field.ErrorText>
            </Field.Root>
            <Button type="submit" size="lg" colorPalette="brand" loading={isSubmitting}>
              Save password
            </Button>
          </form>
        </Stack>
      )}
    </AuthLayout>
  )
}
