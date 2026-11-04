import {
  confirmPasswordReset,
  createUserWithEmailAndPassword,
  EmailAuthProvider,
  GoogleAuthProvider,
  linkWithCredential,
  linkWithPopup,
  sendPasswordResetEmail,
  signInAnonymously,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
  updateProfile,
} from "firebase/auth"
import { accountPatchMe } from "@/client/sdk.gen"
import { auth } from "@/lib/firebase"

const google = () => {
  const provider = new GoogleAuthProvider()
  provider.setCustomParameters({ prompt: "select_account" })
  return provider
}

export const signInDemo = () => signInAnonymously(auth)

export const signInWithEmail = (email: string, password: string) =>
  signInWithEmailAndPassword(auth, email, password)

export const signInWithGoogle = () => signInWithPopup(auth, google())

export async function signUpWithEmail(name: string, email: string, password: string) {
  const { user } = await createUserWithEmailAndPassword(auth, email, password)
  if (name.trim()) {
    await updateProfile(user, { displayName: name.trim() })
    await user.getIdToken(true)
    await accountPatchMe({ body: { display_name: name.trim() } }).catch(() => undefined)
  }
  return user
}

export const requestPasswordReset = (email: string) =>
  sendPasswordResetEmail(auth, email, { url: `${window.location.origin}/login` })

export const completePasswordReset = (code: string, password: string) =>
  confirmPasswordReset(auth, code, password)

/** Keeps the demo's trips and notes: the anonymous Firebase user gains a permanent credential. */
export async function upgradeWithEmail(email: string, password: string) {
  const user = auth.currentUser
  if (!user) throw new Error("Sign in first.")
  const result = await linkWithCredential(user, EmailAuthProvider.credential(email, password))
  await result.user.getIdToken(true)
  return result.user
}

export async function upgradeWithGoogle() {
  const user = auth.currentUser
  if (!user) throw new Error("Sign in first.")
  const result = await linkWithPopup(user, google())
  await result.user.getIdToken(true)
  return result.user
}

export const signOutUser = () => signOut(auth)
