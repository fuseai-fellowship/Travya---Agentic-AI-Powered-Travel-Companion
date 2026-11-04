import { initializeApp } from "firebase/app"
import { connectAuthEmulator, getAuth, signOut } from "firebase/auth"
import type { TokenSource } from "./authFetch"
import { env } from "./env"

export const firebaseApp = initializeApp(env.firebase)
export const auth = getAuth(firebaseApp)

if (env.authEmulatorUrl) {
  connectAuthEmulator(auth, env.authEmulatorUrl, { disableWarnings: true })
}

type Listener = () => void
const expiredListeners = new Set<Listener>()

/** Lets the UI explain why the user was signed out after the API rejected a refreshed token. */
export function onSessionExpired(listener: Listener): () => void {
  expiredListeners.add(listener)
  return () => expiredListeners.delete(listener)
}

export const firebaseTokens: TokenSource = {
  async getToken(forceRefresh) {
    await auth.authStateReady()
    const user = auth.currentUser
    return user ? user.getIdToken(forceRefresh) : null
  },
  onUnauthorized() {
    for (const listener of expiredListeners) listener()
    void signOut(auth)
  },
}

export async function currentUser() {
  await auth.authStateReady()
  return auth.currentUser
}
