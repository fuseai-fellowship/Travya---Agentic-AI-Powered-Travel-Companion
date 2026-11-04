import { Alert, Button, Field, Input, Stack, Text } from "@chakra-ui/react"
import { zodResolver } from "@hookform/resolvers/zod"
import { getRouteApi, Link, useNavigate } from "@tanstack/react-router"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { PasswordInput } from "@/components/PasswordInput"
import { AuthLayout } from "./AuthLayout"
import { signUpWithEmail } from "./actions"
import { firebaseErrorMessage } from "./firebaseErrors"
import { safeRedirect } from "./guard"
import { QuickSignIn } from "./QuickSignIn"

const route = getRouteApi("/signup")

export const signupSchema = z
  .object({
    name: z.string().trim().min(1, "Enter your name").max(120, "Use at most 120 characters"),
    email: z.email("Enter a valid email address"),
    password: z.string().min(8, "Use at least 8 characters"),
    confirm: z.string(),
  })
  .refine((values) => values.password === values.confirm, {
    path: ["confirm"],
    message: "The passwords don't match",
  })
type Values = z.infer<typeof signupSchema>

export function SignupPage() {
  const { redirect } = route.useSearch()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<Values>({ resolver: zodResolver(signupSchema) })

  const onSubmit = handleSubmit(async ({ name, email, password }) => {
    setError(null)
    try {
      await signUpWithEmail(name, email, password)
      await navigate({ href: safeRedirect(redirect) })
    } catch (caught) {
      setError(firebaseErrorMessage(caught))
    }
  })

  return (
    <AuthLayout
      title="Create Your Account"
      subtitle="Join us today and get started"
      footer={
        <Text>
          Already have an account?{" "}
          <Link to="/login" search={{ redirect }} style={{ fontWeight: 600 }}>
            Sign in
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
          <Field.Root invalid={!!errors.name}>
            <Field.Label>Full name</Field.Label>
            <Input
              autoComplete="name"
              placeholder="Enter your full name"
              size="lg"
              {...register("name")}
            />
            <Field.ErrorText>{errors.name?.message}</Field.ErrorText>
          </Field.Root>
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
              autoComplete="new-password"
              placeholder="Create a password"
              size="lg"
              {...register("password")}
            />
            <Field.ErrorText>{errors.password?.message}</Field.ErrorText>
          </Field.Root>
          <Field.Root invalid={!!errors.confirm}>
            <Field.Label>Confirm password</Field.Label>
            <PasswordInput
              autoComplete="new-password"
              placeholder="Confirm your password"
              size="lg"
              {...register("confirm")}
            />
            <Field.ErrorText>{errors.confirm?.message}</Field.ErrorText>
          </Field.Root>
          <Button
            type="submit"
            size="lg"
            colorPalette="brand"
            loading={isSubmitting}
            loadingText="Creating account…"
          >
            Create account
          </Button>
        </form>
      </Stack>
      <QuickSignIn redirectTo={redirect} />
    </AuthLayout>
  )
}
