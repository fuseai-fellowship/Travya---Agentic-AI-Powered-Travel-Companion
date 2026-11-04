import { Button, type ButtonProps, HStack, Separator, Stack, Text } from "@chakra-ui/react"
import { useNavigate } from "@tanstack/react-router"
import { useState } from "react"
import { LuSparkles } from "react-icons/lu"
import { GoogleMark } from "@/components/GoogleMark"
import { toaster } from "@/components/ui/toaster"
import { signInDemo, signInWithGoogle } from "./actions"
import { firebaseErrorMessage, isPopupDismissed } from "./firebaseErrors"
import { safeRedirect } from "./guard"

function useSignIn(action: () => Promise<unknown>, redirectTo?: string) {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const run = async () => {
    setLoading(true)
    try {
      await action()
      await navigate({ href: safeRedirect(redirectTo) })
    } catch (error) {
      if (!isPopupDismissed(error)) {
        toaster.create({
          type: "error",
          title: "Couldn't sign in",
          description: firebaseErrorMessage(error),
        })
      }
    } finally {
      setLoading(false)
    }
  }
  return { run, loading }
}

export function DemoButton({ redirectTo, ...props }: ButtonProps & { redirectTo?: string }) {
  const { run, loading } = useSignIn(signInDemo, redirectTo)
  return (
    <Button
      colorPalette="brand"
      loading={loading}
      loadingText="Starting demo…"
      onClick={run}
      {...props}
    >
      <LuSparkles /> Try the demo — no sign-up
    </Button>
  )
}

export function GoogleButton({ redirectTo, ...props }: ButtonProps & { redirectTo?: string }) {
  const { run, loading } = useSignIn(signInWithGoogle, redirectTo)
  return (
    <Button variant="outline" loading={loading} onClick={run} {...props}>
      <GoogleMark /> Continue with Google
    </Button>
  )
}

export function QuickSignIn({ redirectTo }: { redirectTo?: string }) {
  return (
    <Stack gap="3">
      <HStack gap="3">
        <Separator flex="1" />
        <Text fontSize="xs" color="fg.muted" textTransform="uppercase" letterSpacing="wider">
          or
        </Text>
        <Separator flex="1" />
      </HStack>
      <GoogleButton redirectTo={redirectTo} size="lg" />
      <DemoButton redirectTo={redirectTo} size="lg" variant="subtle" />
    </Stack>
  )
}
