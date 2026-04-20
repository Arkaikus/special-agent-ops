---
name: create-team
description: Discover project stack and scaffold a specialized multi-agent team with a /team manifest
---

# /create-team

Bootstrap a specialized multi-agent team for the current project.

## Signature

`/create-team [--dry-run] [--team-name <name>] [--model <model-id>] [--output <path>]`

### Flags

- `--dry-run` (default: `false`) — preview output only, do not write files.
- `--team-name` (default: derived from project name) — override generated team identifier.
- `--model` (default: host default) — force a specific model for all generated agents.
- `--output` (default: `.cursor/` or `.claude/`) — destination root for generated files.

## Behavior

Follow these phases in order.

### Phase 1 — Project Discovery

1. Perform a non-recursive root scan for stack indicators:
   - Runtime/build files: `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`, `build.gradle`, `composer.json`, `*.csproj`
   - Infra: `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `terraform/`, `infra/`, `.github/workflows/`, root `*.yml`
   - Docs and agent context: `README.md`, `ARCHITECTURE.md`, `docs/`, `.cursor/`, `.claude/`, `.github/copilot/`
2. If present, perform second-level scan under: `src/`, `app/`, `lib/`, `packages/`, `services/`.
3. Build a stack profile object with this schema:

```json
{
  "project_name": "my-app",
  "languages": ["TypeScript", "Python"],
  "runtimes": ["Node.js 20", "Python 3.12"],
  "frameworks": ["Next.js 14", "FastAPI"],
  "test_frameworks": ["Vitest", "Pytest"],
  "infrastructure": ["Docker", "GitHub Actions"],
  "has_db": true,
  "db_type": "PostgreSQL",
  "monorepo": false,
  "existing_agents_dir": ".cursor/agents/",
  "existing_skills": ["@typescript", "@testing"],
  "documentation_present": true
}
```

#### Empty/unrecognized project flow

If no stack indicators are found, pause and present:

```text
⚠️  This project folder appears to be empty or unrecognized.

What would you like to do?

  [1] Describe your project in plain language and I'll scaffold from scratch
  [2] Choose a starter template (web app / API / CLI / data pipeline / monorepo)
  [3] Point me to an existing codebase directory
  [4] Cancel
```

Then:
- Option 1: collect freeform description, infer stack, continue with synthetic profile.
- Option 2: present template menu, apply selected template.
- Option 3: rerun Phase 1 against user-provided path.
- Option 4: abort cleanly.

### Phase 2 — Existing Configuration Audit

Inspect and reconcile existing assets before creating new ones.

Audit sources:
- `.cursor/agents/*.md` or `.claude/agents/*.md`
- `.cursor/rules/*.md` or `.claude/rules/*.md`
- `.cursor/skills/`
- `.claude/commands/*.md`
- `AGENTS.md` or `CLAUDE.md` in root

Reconciliation:
- Exact role match: **REUSE** existing agent as-is; tag as `existing`.
- Partial role overlap: **EXTEND** from existing agent via include/reference.
- Relevant skills: **SYMLINK** to shared skills where possible.
- Name collision with incompatible behavior: **WARN** and require resolution (overwrite / rename / skip).

Skill reuse convention:
- Cursor (symlink preferred): `.cursor/teams/<team-name>/skills/@typescript -> ../../skills/@typescript`
- Claude/no-symlink fallback: `.ref.md` reference file:

```markdown
@import ../../skills/@typescript
```

### Phase 3 — Team Composition

Always include `architect`.

Map detected stack to roles:
- Frontend framework → `ui-engineer`
- Backend/API → `api-engineer`
- Database/ORM → `data-engineer`
- Testing framework present → `qa-engineer`
- Infra/CI files → `devops-engineer`
- Documentation present → `tech-writer`
- Monorepo/package complexity → `platform-engineer`
- Auth/secrets/security-sensitive surface → `security-reviewer`
- Data science/ML indicators (`.ipynb`, `model/`, etc.) → `ml-engineer`

If stack is still unrecognized, fall back to:
- `architect`
- `generalist-engineer`
- `qa-engineer`

Write each role to:
- `.cursor/teams/<team-name>/agents/<role>.md` (or `.claude/...`)

Use this structure:

```markdown
---
name: <role>
team: <team-name>
version: 1.0.0
stack: [<relevant stack keys>]
skills: [<linked/referenced skills>]
model: <model-id or "default">
---

# <Role Display Name>

## Responsibilities
- <Role-specific responsibilities from stack profile>

## Context Rules
- Always read <primary config file> before responding
- Scope responses to <relevant src path> unless asked otherwise
- Escalate cross-cutting concerns to `architect`

## Specialization Prompt
You are a <Role> working on a <stack summary> project called "<project_name>".
Your primary concern is <domain>. Use these skills: <skills list>.
When uncertain about architecture, defer via `/team architect`.
```

Architect special requirements:
- Include serialized full stack profile.
- Include full team roster and responsibilities.
- Include routing/delegation rules.
- Include summary of discovered existing agents/skills.

### Phase 4 — `/team` Command Generation

Write command manifest to `.cursor/commands/team.md` or `.claude/commands/team.md`.

Required content:
- `/team <role> [task description]` usage
- table of available agents
- routing rules:
  - no role → `architect`
  - multi-role tasks orchestrated by `architect`
  - case-insensitive role names + aliases (`fe`, `frontend` → `ui-engineer`)
- examples for architect, ui, qa, devops tasks

### Phase 4.2 — Team Index

Write `.cursor/teams/<team-name>/README.md` (or `.claude/...`) including:
- generation timestamp
- readable stack profile summary
- agents list + one-line descriptions
- linked/referenced skills list
- reused existing assets
- usage instructions for `/team` and `/team <role>`

### Phase 5 — Output Summary

Display a structured completion summary:
- Team name
- output location
- agents created
- reused assets
- command registration path
- final “Run `/team` to get started.”

If `--dry-run` is enabled, prefix each line with `[DRY RUN]` and write nothing.

### Phase 6 — Optional Post-Generation Hooks

If `.cursor/hooks/` or `.claude/hooks/` exists (or host supports hooks), create stubs:
- `on_file_save` → route `src/` file changes to relevant specialist
- `on_pr_open` → invoke architect for review routing
- `on_test_fail` → route failure context to `qa-engineer`

Do not auto-enable hooks.

## Error Handling

- Unknown stack: use minimal fallback team.
- Existing agent name collision: show diff and prompt overwrite/rename/skip.
- Missing write permissions to output root: abort with clear chmod-style guidance.
- Unavailable model from `--model`: warn and fall back to host default.
- Circular symlink detected: skip symlink, copy file, and log warning.

## Host Environment Notes

- **GitHub Copilot Workspace**: may use `.github/copilot/` as alternate root.
- **Cursor**: prefer symlinks on macOS/Linux; `.ref.md` fallback where needed.
- **Claude Projects**: use `.claude/`; prefer `.ref.md` references over symlinks.

## Extensibility

- Users can add custom roles by dropping `<role>.md` into team `agents/` and adding `/team` entry.
- Team index includes a version field for future upgrade/diff flows.
- Multiple teams may coexist under `.cursor/teams/`; `/team` defaults to most recently active team unless overridden.
