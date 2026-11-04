# Security policy

## Reporting a vulnerability

Please report vulnerabilities privately through GitHub:
**Security → Report a vulnerability** on this repository
([direct link](https://github.com/fuseai-fellowship/Travya---Agentic-AI-Powered-Travel-Companion/security/advisories/new)).

Do not open a public issue, pull request or discussion for a security problem.

Include what you can of:

- the affected endpoint, page or file, and the version or commit;
- steps to reproduce or a proof of concept;
- the impact you expect (data exposure, account takeover, cost abuse of the LLM budget, ...).

You can expect an acknowledgement within 7 days and a status update within 14 days. Fixes ship from
`main`; there are no maintained older release lines.

## Scope

In scope: the code in this repository and the hosted deployment linked from the README.
Out of scope: third-party services the app calls (Firebase, Gemini, OpenStreetMap services, Unsplash),
denial of service by volume, and findings that need a compromised device or account.

## Handling secrets

No secret belongs in this repository. Production secrets live in Google Secret Manager, deploys
authenticate with Workload Identity Federation, and `gitleaks` runs in pre-commit. If you find a
credential in the code or its history, report it as above so it can be revoked.
