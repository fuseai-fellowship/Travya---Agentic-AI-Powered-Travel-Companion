const MESSAGES: Record<string, string> = {
  "auth/invalid-credential": "That email and password don't match an account.",
  "auth/wrong-password": "That email and password don't match an account.",
  "auth/user-not-found": "That email and password don't match an account.",
  "auth/invalid-email": "Enter a valid email address.",
  "auth/email-already-in-use": "An account with this email already exists. Sign in instead.",
  "auth/credential-already-in-use": "That account is already linked to another Travya user.",
  "auth/provider-already-linked": "This account is already linked.",
  "auth/weak-password": "Use a password with at least 8 characters.",
  "auth/too-many-requests": "Too many attempts. Wait a minute and try again.",
  "auth/network-request-failed": "Can't reach the sign-in service. Check your connection.",
  "auth/popup-blocked": "Your browser blocked the sign-in window. Allow pop-ups and try again.",
  "auth/popup-closed-by-user": "The sign-in window was closed before finishing.",
  "auth/cancelled-popup-request": "The sign-in window was closed before finishing.",
  "auth/operation-not-allowed": "This sign-in method isn't enabled for the demo.",
  "auth/admin-restricted-operation": "Demo sign-in is turned off right now.",
  "auth/requires-recent-login": "For security, sign in again before doing this.",
  "auth/expired-action-code": "This reset link has expired. Request a new one.",
  "auth/invalid-action-code": "This reset link is invalid or was already used.",
}

export function firebaseErrorCode(error: unknown): string {
  return typeof error === "object" && error !== null && "code" in error
    ? String((error as { code: unknown }).code)
    : ""
}

export function firebaseErrorMessage(error: unknown): string {
  return MESSAGES[firebaseErrorCode(error)] ?? "Sign-in failed. Please try again."
}

/** Closing the popup yourself isn't an error worth a red toast. */
export function isPopupDismissed(error: unknown): boolean {
  const code = firebaseErrorCode(error)
  return code === "auth/popup-closed-by-user" || code === "auth/cancelled-popup-request"
}
