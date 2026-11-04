import { redirect } from "@tanstack/react-router"

/** Only same-site paths are allowed as post-login targets (no `//evil.com`, no absolute URLs). */
export function safeRedirect(target: unknown, fallback = "/trips"): string {
  if (typeof target !== "string") return fallback
  if (!target.startsWith("/") || target.startsWith("//") || target.startsWith("/\\"))
    return fallback
  return target
}

/** `beforeLoad` guard for signed-in areas: unknown users go to /login and come back afterwards. */
export async function requireUser(
  getUser: () => Promise<unknown>,
  returnTo: string,
): Promise<void> {
  const user = await getUser()
  if (!user) {
    throw redirect({ to: "/login", search: { redirect: returnTo } })
  }
}

/** `beforeLoad` for the sign-in pages: signed-in users skip straight to the app. */
export async function redirectIfSignedIn(
  getUser: () => Promise<unknown>,
  target: unknown,
): Promise<void> {
  if (await getUser()) {
    throw redirect({ href: safeRedirect(target) })
  }
}
