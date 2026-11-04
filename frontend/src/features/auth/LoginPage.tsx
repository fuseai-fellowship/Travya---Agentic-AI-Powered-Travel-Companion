import { Alert, Box, Button, Field, Input, Stack, Text } from "@chakra-ui/react"
import { zodResolver } from "@hookform/resolvers/zod"
import { getRouteApi, Link, useNavigate } from "@tanstack/react-router"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { PasswordInput } from "@/components/PasswordInput"
import { AuthLayout } from "./AuthLayout"
import { signInWithEmail } from "./actions"
import { firebaseErrorMessage } from "./firebaseErrors"
import { safeRedirect } from "./guard"
import { QuickSignIn } from "./QuickSignIn"

const route = getRouteApi("/login")

const schema = z.object({
  email: z.email("Enter a valid email address"),
  password: z.string().min(1, "Enter your password"),
})
type Values = z.infer<typeof schema>

export function LoginPage() {
  const { redirect } = route.useSearch()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<Values>({ resolver: zodResolver(schema) })

  const onSubmit = handleSubmit(async ({ email, password }) => {
    setError(null)
    try {
      await signInWithEmail(email, password)
      await navigate({ href: safeRedirect(redirect) })
    } catch (caught) {
      setError(firebaseErrorMessage(caught))
    }
  })

  return (
    <AuthLayout
      title="Welcome Back"
      subtitle="Sign in to your account to continue"
      footer={
        <Text>
          Don't have an account?{" "}
          <Link to="/signup" search={{ redirect }} style={{ fontWeight: 600 }}>
            Create account
          </Link>
        </Text>
      }
    >
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
          <Field.Root invalid={!!errors.password}>
            <Field.Label>Password</Field.Label>
            <PasswordInput
              autoComplete="current-password"
              placeholder="Enter your password"
              size="lg"
              {...register("password")}
            />
            <Field.ErrorText>{errors.password?.message}</Field.ErrorText>
          </Field.Root>
          <Box alignSelf="flex-end" fontSize="sm">
            <Link to="/reset-password">Forgot your password?</Link>
          </Box>
          <Button
            type="submit"
            size="lg"
            colorPalette="brand"
            loading={isSubmitting}
            loadingText="Signing in…"
          >
            Sign In
          </Button>
        </form>
      </Stack>
      <QuickSignIn redirectTo={redirect} />
    </AuthLayout>
  )
}
