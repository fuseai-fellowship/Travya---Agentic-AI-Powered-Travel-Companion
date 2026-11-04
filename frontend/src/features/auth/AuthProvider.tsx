import { useQueryClient } from "@tanstack/react-query"
import { onIdTokenChanged } from "firebase/auth"
import { createContext, type ReactNode, useContext, useEffect, useRef, useState } from "react"
import { toaster } from "@/components/ui/toaster"
import { auth, onSessionExpired } from "@/lib/firebase"

export interface SessionUser {
  uid: string
  isAnonymous: boolean
  email: string | null
  displayName: string | null
  providers: string[]
}

export type AuthStatus = "loading" | "signedIn" | "signedOut"

interface AuthValue {
  status: AuthStatus
  user: SessionUser | null
}

const AuthContext = createContext<AuthValue>({ status: "loading", user: null })

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [value, setValue] = useState<AuthValue>({ status: "loading", user: null })
  const lastUid = useRef<string | null>(null)

  useEffect(
    () =>
      onIdTokenChanged(auth, (user) => {
        if (lastUid.current && lastUid.current !== user?.uid) queryClient.clear()
        lastUid.current = user?.uid ?? null
        setValue(
          user
            ? {
                status: "signedIn",
                user: {
                  uid: user.uid,
                  isAnonymous: user.isAnonymous,
                  email: user.email,
                  displayName: user.displayName,
                  providers: user.providerData.map((info) => info.providerId),
                },
              }
            : { status: "signedOut", user: null },
        )
      }),
    [queryClient],
  )

  useEffect(
    () =>
      onSessionExpired(() =>
        toaster.create({
          type: "warning",
          title: "Signed out",
          description: "Your session ended. Please sign in again.",
        }),
      ),
    [],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthValue {
  return useContext(AuthContext)
}
