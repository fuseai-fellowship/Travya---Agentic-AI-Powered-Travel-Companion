## What and why

<!-- One or two sentences. Link the issue: Closes #123 -->

## How it was tested

<!-- Commands run, screenshots for UI changes. -->

## Checklist

- [ ] PR title follows Conventional Commits (`feat: ...`, `fix(api): ...`); it becomes the squash commit
- [ ] Tests added or updated, and `make lint test` passes locally
- [ ] Migrations included for model changes (`make revision m="..."`), and they apply to an empty database
- [ ] API changes: client regenerated (`make client`)
- [ ] No secrets, keys or personal data in code, fixtures or logs
- [ ] Docs updated where behaviour changed
