/**
 * Environment of the compose `e2e` service (see compose.yaml). The base URL itself is read by
 * playwright.config.ts from PLAYWRIGHT_BASE_URL or E2E_BASE_URL.
 */
export const e2eEnv = {
  apiUrl: process.env.E2E_API_URL || "http://localhost:8000",
  authEmulatorHost: process.env.FIREBASE_AUTH_EMULATOR_HOST || "localhost:9099",
  firebaseProjectId: process.env.FIREBASE_PROJECT_ID || "demo-travya",
}

/** Creates an email/password user directly in the Auth emulator (no UI, no real email). */
export async function createEmulatorUser(email: string, password: string) {
  const url = `http://${e2eEnv.authEmulatorHost}/identitytoolkit.googleapis.com/v1/accounts:signUp?key=demo-key`
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, returnSecureToken: true }),
  })
  if (!response.ok) throw new Error(`Auth emulator sign-up failed: ${response.status}`)
}

/** True when the API answers its readiness probe; specs that need it can skip otherwise. */
export async function apiReady(): Promise<boolean> {
  try {
    const response = await fetch(`${e2eEnv.apiUrl}/api/v1/health/ready`)
    return response.ok
  } catch {
    return false
  }
}

export const uniqueEmail = (prefix: string) =>
  `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@example.test`
