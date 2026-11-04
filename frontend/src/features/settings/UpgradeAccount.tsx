import { Alert, Button, Field, Input, Stack, Text } from "@chakra-ui/react"
import { zodResolver } from "@hookform/resolvers/zod"
import { useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { GoogleMark } from "@/components/GoogleMark"
import { PasswordInput } from "@/components/PasswordInput"
import type { SessionUser } from "@/features/auth/AuthProvider"
import { upgradeWithEmail, upgradeWithGoogle } from "@/features/auth/actions"
import { firebaseErrorMessage, isPopupDismissed } from "@/features/auth/firebaseErrors"
import { notifySuccess } from "@/lib/notify"
import { invalidateOperations } from "@/lib/queryKeys"

const schema = z.object({
  email: z.email("Enter a valid email address"),
  password: z.string().min(8, "Use at least 8 characters"),
})
type Values = z.infer<typeof schema>

const PROVIDER_NAMES: Record<string, string> = {
  password: "Email and password",
  "google.com": "Google",
}

/** Anonymous demo users keep their trips by linking an email/password or Google credential. */
export function UpgradeAccount({ user }: { user: SessionUser }) {
  const queryClient = useQueryClient()
  const [error, setError] = useState<string | null>(null)
  const [googleBusy, setGoogleBusy] = useState(false)
  const { register, handleSubmit, formState } = useForm<Values>({ resolver: zodResolver(schema) })

  if (!user.isAnonymous) {
    return (
      <Text>
        Signed in as <strong>{user.email ?? user.displayName ?? "you"}</strong>
        {user.providers.length > 0 && (
          <Text as="span" color="fg.muted">
            {" "}
            with {user.providers.map((id) => PROVIDER_NAMES[id] ?? id).join(" and ")}
          </Text>
        )}
        .
      </Text>
    )
  }

  const done = async () => {
    await invalidateOperations(queryClient, "accountReadMe")
    notifySuccess("Account saved", "Your demo trips are now kept with this sign-in.")
  }

  const linkGoogle = async () => {
    setError(null)
    setGoogleBusy(true)
    try {
      await upgradeWithGoogle()
      await done()
    } catch (caught) {
      if (!isPopupDismissed(caught)) setError(firebaseErrorMessage(caught))
    } finally {
      setGoogleBusy(false)
    }
  }

  return (
    <Stack gap="4">
      <Alert.Root status="warning" borderRadius="card">
        <Alert.Indicator />
        <Alert.Content>
          <Alert.Title>You're using a demo account</Alert.Title>
          <Alert.Description>
            Signing out or clearing this browser loses your trips. Save them by adding a sign-in.
          </Alert.Description>
        </Alert.Content>
      </Alert.Root>
      {error && (
        <Alert.Root status="error" size="sm">
          <Alert.Indicator />
          <Alert.Title>{error}</Alert.Title>
        </Alert.Root>
      )}
      <Button
        variant="outline"
        alignSelf="flex-start"
        loading={googleBusy}
        onClick={() => void linkGoogle()}
      >
        <GoogleMark /> Save with Google
      </Button>
      <Stack asChild gap="3">
        <form
          noValidate
          onSubmit={handleSubmit(async ({ email, password }) => {
            setError(null)
            try {
              await upgradeWithEmail(email, password)
              await done()
            } catch (caught) {
              setError(firebaseErrorMessage(caught))
            }
          })}
        >
          <Field.Root invalid={!!formState.errors.email}>
            <Field.Label>Email</Field.Label>
            <Input type="email" autoComplete="email" {...register("email")} />
            <Field.ErrorText>{formState.errors.email?.message}</Field.ErrorText>
          </Field.Root>
          <Field.Root invalid={!!formState.errors.password}>
            <Field.Label>Password</Field.Label>
            <PasswordInput autoComplete="new-password" {...register("password")} />
            <Field.ErrorText>{formState.errors.password?.message}</Field.ErrorText>
          </Field.Root>
          <Button
            type="submit"
            colorPalette="brand"
            alignSelf="flex-start"
            loading={formState.isSubmitting}
          >
            Save with email
          </Button>
        </form>
      </Stack>
    </Stack>
  )
}
