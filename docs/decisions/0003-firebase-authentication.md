# 0003. Use Firebase Authentication

- Status: accepted
- Date: 2026-11-04

## Context

The prototype inherited a template login: password hashing, custom JWTs stored in `localStorage`, SMTP
for password resets, e-mail templates and an admin user model. It accepted the example `SECRET_KEY`,
and a stored XSS in the notes page could read the token. A portfolio demo also needs a zero-friction
"try it now" path, and it should not store passwords at all.

## Decision

Delegate identity to [Firebase Authentication](https://firebase.google.com/docs/auth):

- the web app signs users in with the Firebase SDK: email and password, Google, and anonymous
  sessions for "Try the demo";
- the API only verifies ID tokens with firebase-admin (`backend/app/core/security.py`) and maps the
  token's uid to a local `users` row created on the first request (`services/users.py`);
- an anonymous account upgraded to email or Google keeps its uid, so its data carries over;
- administrator rights, if ever needed, come from a Firebase custom claim (`admin`);
- locally the Firebase Auth emulator runs in Compose under the demo project `demo-travya`, so
  development and CI need no Firebase project;
- deleting an account deletes the user's rows, files and Firebase user.

## Consequences

- No password storage, reset e-mails or token signing in the codebase.
- Bearer tokens instead of cookies: no CSRF surface on the API.
- Anonymous sessions make the demo usable in one click; per-user limits still apply to them.
- The free tier covers the expected usage.
- Identity depends on one vendor; the local `users` table keeps application data independent of it.
- Tokens are verified without a revocation check, so a revoked token is accepted until it expires
  (at most an hour).
- Anyone can create anonymous accounts, so per-user limits alone cannot cap total usage; the global
  daily LLM budget does.

## Alternatives considered

- **Keep the custom JWT stack**: the most code to secure and maintain, and still no anonymous mode.
- **Auth0 or Clerk**: comparable features, but a separate vendor from the rest of the Google stack and
  tighter free tiers.
- **Supabase Auth**: a good fit with Postgres, but it would pull in a second platform next to Neon.
