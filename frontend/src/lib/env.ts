/** Build-time configuration. Blank values (e.g. an unset Docker build arg) count as unset. */
export function readEnv(value: string | undefined): string | undefined {
  const trimmed = value?.trim()
  return trimmed ? trimmed : undefined
}

const vars = import.meta.env

export const env = {
  apiUrl: (readEnv(vars.VITE_API_URL) ?? "http://localhost:8000").replace(/\/+$/, ""),
  firebase: {
    apiKey: readEnv(vars.VITE_FIREBASE_API_KEY) ?? "demo-key",
    authDomain: readEnv(vars.VITE_FIREBASE_AUTH_DOMAIN) ?? "localhost",
    projectId: readEnv(vars.VITE_FIREBASE_PROJECT_ID) ?? "demo-travya",
  },
  authEmulatorUrl: readEnv(vars.VITE_FIREBASE_AUTH_EMULATOR_URL),
} as const

export const REPO_URL =
  "https://github.com/fuseai-fellowship/Travya---Agentic-AI-Powered-Travel-Companion"
