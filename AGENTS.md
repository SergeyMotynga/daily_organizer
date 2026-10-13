# Daily Organizer Agent Rules

This file defines how AI coding agents must work in the Daily Organizer repository.

## Language

- Talk to the user in Russian.
- Keep user-facing explanations concise, direct, and practical.
- Code identifiers must be in English.
- Backend docstrings and code comments should be in Russian, following the current project style.
- Project documentation for the user should stay in Russian unless the user explicitly asks otherwise.
- Agent/system instructions may be written in English for consistency and model reliability.

## Read First

Before making changes, read:

- `README.md`
- `docs/project.md`
- `docs/development/git-flow.md`
- `docs/development/codex-working-rules.md`
- relevant files under `docs/version/v0.1/`, if present

If the task changes product behavior, API contracts, database structure, UX rules, or technical decisions, treat Notion as the source of truth and mention what should be updated there.

## Git Flow

- Before selecting/creating a branch, committing, pushing, or handling a PR, read `docs/development/git-flow.md`. It is the repository source of truth for branch naming, base/target branches, delivery permissions, and PR format.
- In the user's local environment, also read `C:/Users/motyn/.codex/workflows/git-delivery.md` when available for delivery tooling and templates.
- Make changes in a working branch; preserve existing user changes. Start a new task from current `develop` after the previous PR is merged or closed.
- The user has standing authorization for commits, ordinary working-branch push, and draft PR delivery of completed tasks. Follow the documented delivery process without asking for the same authorization again. Separate explicit authorization is required for merge, draft-to-ready, force-push, rewriting others' history, and branch deletion.

## Backend Architecture

Backend follows this layering:

```text
API layer -> service layer -> repository/ORM layer
```

Layer boundaries:

- `api/` - endpoints, dependencies, Query/Path params, request/response mapping.
- `schemas/` - HTTP request/response Pydantic schemas only.
- `dto/` - internal dataclasses/DTOs between layers, never HTTP schemas.
- `services/` - business logic and transaction boundaries.
- `repositories/` - database queries only, no `commit`/`rollback`, no business decisions.
- `models/` - SQLAlchemy ORM models.
- `domain/` - domain enums/value constants.
- `validators/` - reusable domain validation.
- `exceptions/` - domain exceptions.

Do not:

- put HTTP schemas into `dto/`;
- put business logic into `api/`;
- put `commit`/`rollback` into repositories;
- add abstractions only for aesthetics;
- change public API contracts without an explicit user decision;
- add dependencies without stopping and explaining why.

## Work Style

- Move in small steps.
- One meaningful patch should change one file unless the user allows otherwise.
- After each patch, explain why the change belongs to that layer.
- If the user asks "why", explain first; do not silently change direction.
- If Notion/spec/code disagree, stop and ask.

## Subagents

Subagents are available roles, not a mandatory pipeline.

Default mode: one main agent works alone.

Use subagents only when there is a clear reason:

- the task is large and can be safely split;
- independent review is useful;
- the main agent is uncertain or stuck;
- a PR needs final review;
- frontend output needs visual review.

Limits:

- ordinary task: at most 1 subagent;
- complex backend/auth/frontend task: at most 2 subagents;
- do not run multiple writing agents at the same time;
- prefer read-only reviewers over extra writing agents.

Role selection:

- `backend_worker` - small backend implementation patches.
- `frontend_worker` - frontend screens and components.
- `architecture_reviewer` - layer and structure review.
- `test_reviewer` - tests, fixtures, helpers, and coverage review.
- `security_reviewer` - auth, cookies, CORS, secrets, permissions, user data access.
- `ui_reviewer` - visual frontend review from screenshots/mockups.
- `pr_reviewer` - final read-only PR review.
- `docs_notion_helper` - docs/Notion update summary.

Do not run:

- `security_reviewer` unless the task touches auth/cookies/CORS/secrets/permissions/user data/dependencies;
- `ui_reviewer` unless there is visible frontend/UI output;
- `test_reviewer` unless tests changed or critical backend behavior changed;
- `architecture_reviewer` unless files cross layers, structure changes, or new abstractions appear;
- `pr_reviewer` before the diff is ready for PR.

## Stop Signals

Stop and ask the user if:

- the base/target branch remains ambiguous after reading the Git flow rules;
- the change needs more files than allowed;
- a new dependency is needed;
- a migration is needed;
- auth/security/cookies/CORS must change;
- public API must change;
- a file must be deleted or renamed;
- layer architecture must change;
- Notion/spec conflicts with code;
- tests still fail after two fix attempts;
- a Git action requires authorization not already granted by the user, as defined in `docs/development/git-flow.md`.

## Frontend Workflow

For frontend work, the user does not need to review every CSS/TSX line.

The agent should:

- implement the screen/component from the mockup;
- run the frontend;
- capture screenshots;
- compare against the mockup;
- fix obvious visual issues;
- show the user the result and notable differences.

## Checks

Backend:

```powershell
task backend:check
task backend:test-cov
```

Docker DB:

```powershell
task docker:up
task docker:down
```

If `task` is unavailable in the agent environment, run equivalent commands from `backend/.venv` and say so explicitly.
