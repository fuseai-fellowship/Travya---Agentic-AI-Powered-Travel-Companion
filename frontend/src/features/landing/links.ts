import { REPO_URL } from "@/lib/env"

const blob = (path: string) => `${REPO_URL}/blob/main/${path}`

export const LINKS = {
  repo: REPO_URL,
  stars: `${REPO_URL}/stargazers`,
  issues: `${REPO_URL}/issues`,
  evals: blob("docs/evals.md"),
  evalRunner: blob("backend/evals/run.py"),
  goldenTrips: blob("backend/evals/golden_trips.json"),
  checks: blob("backend/app/agents/planning/checks.py"),
  pipeline: blob("backend/app/agents/planning/pipeline.py"),
  planning: blob("backend/app/services/planning.py"),
  isolation: blob("backend/tests/api/test_isolation.py"),
  ratelimit: blob("backend/app/core/ratelimit.py"),
  offers: blob("backend/app/integrations/offers/sample.py"),
  security: blob("docs/security.md"),
  contributing: blob("CONTRIBUTING.md"),
  license: blob("LICENSE"),
  docs: "https://travya-docs.pages.dev/",
  author: "https://github.com/parajulitilak",
  fuseai: "https://github.com/fuseai-fellowship",
} as const
