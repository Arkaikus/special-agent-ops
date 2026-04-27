# special-agent-ops

**agentctl** is a small kubectl-style CLI for **agent YAML manifests**: validate manifests, generate code (Pydantic AI, MCP, or Rust swarm), and **deploy** agents as Docker images wired into Compose. A **FastAPI agent-gateway** and **Vite frontend** provide projects, a kanban board, registered agents, and HTTP invoke against running agents.

The repo also includes a **Cursor/Claude command** that scans a project and scaffolds a specialized agent team. See [Available command specs](#available-command-specs) below.

## Main features

- **Manifest-driven agents** — Declarative `apiVersion: agentctl/v1` YAML: model backends, system prompts, optional MCP servers, skills, workspace volumes, and opt-in filesystem tools (`ls`, `grep`, `edit`, `glob`, optional `bash`).
- **agentctl** — `apply` writes generated code under `.agents/{name}/` (server, Dockerfile, `compose.agent.yml`, resolved manifest). `deploy` builds the image and `docker compose up` with the root `docker-compose.yml` plus the agent fragment. `doctor` checks Docker and related tools.
- **Runtimes** — `pydantic-ai` (default), `mcp-agent`, and `swarm-rs` (Rust) via codegen.
- **Model backends** — `anthropic`, `ollama`, and `openai_compatible` (LM Studio, OpenAI-compatible APIs, and similar).
- **MCP** — `stdio`, `sse`, or `http` transports; env-injected headers or bearer tokens for remote servers.
- **agent-gateway** — REST API: health, projects (with default board columns), board/columns/cards, agent registration and listing, and **invoke** to call a deployed agent by registered id/name or ad hoc host/port. Uses SQLite and a Redis bus for async coordination.
- **Frontend** — React/Vite UI: projects, per-project board, agents, and agent chat; expects the gateway (default `VITE_GATEWAY_URL=http://localhost:8000`).

## Quick start (CLI)

Requires **Python 3.13+** and **Docker** for deploys.

```bash
# From the repo root
uv sync
uv run agentctl doctor
```

Apply a manifest and deploy (example: demo agent using Ollama on the host):

```bash
uv run agentctl apply examples/agents/demo.yaml
uv run agentctl deploy demo
```

- First apply to an existing `.agents/{name}/` output requires **`--force`** (or use `deploy --apply`, which runs apply with force when a matching `examples/agents/{name}.yaml` exists).
- `deploy --apply` runs apply first, then build and compose: `uv run agentctl deploy demo --apply`.

## Configuration

Copy **`.env.example`** to **`.env`** and set what you use:

- **Gateway** — `GATEWAY_DATABASE_URL`, `GATEWAY_REDIS_URL`, `GATEWAY_CORS_ORIGINS` (defaults suit local dev).
- **Models** — `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, or host Ollama and point agents at `http://host.docker.internal:11434/v1` from Linux containers.
- **Gitea MCP** (optional) — `GITEA_ACCESS_TOKEN` after completing the Gitea install wizard; used by the gitea-mcp example.

Frontend env: see **`frontend/.env.example`** (`VITE_GATEWAY_URL`).

## Local stack (Docker Compose)

```bash
docker compose up -d
```

Typical URLs:

- **Frontend** — http://localhost:5173 (gateway URL via `VITE_GATEWAY_URL`, default `http://localhost:8000`)
- **Gateway** — http://localhost:8000 (health: `GET /health`)
- **Gitea** — http://localhost:3000 (first-run setup, then create a PAT for `GITEA_ACCESS_TOKEN`)
- **Gitea MCP** (profile `mcp`) — e.g. http://localhost:8088 (see `docker-compose.yml` port mapping for `gitea-mcp`)
- **LM Studio** — optional `lmstudio-proxy` forward on host `1234` so agents in Docker can reach a host listener

Run the gateway without Compose:

```bash
uv run agent-gateway
```

## agentctl commands

| Command | Purpose |
|--------|---------|
| `agentctl apply <manifest.yaml>` | Validate manifest; emit `.agents/{name}/` (codegen, Dockerfile, `compose.agent.yml`, `manifest.resolved.yaml`). Add `--dry-run` or `--force` as needed. |
| `agentctl deploy <name>` | Build `agentctl/{name}:local` from `.agents/{name}/` and run the Compose service. `--apply` applies `examples/agents/{name}.yaml` first; `-f` sets a custom manifest. `--no-compose` builds only. |
| `agentctl doctor` | Sanity-check Docker and tooling. |

## Agent examples (`examples/agents/`)

| File | What it shows |
|------|----------------|
| [`demo.yaml`](examples/agents/demo.yaml) | **Ollama** + Pydantic AI, minimal—good first deploy. |
| [`researcher.yaml`](examples/agents/researcher.yaml) | **Anthropic** (set `ANTHROPIC_API_KEY`). |
| [`lmstudio.yaml`](examples/agents/lmstudio.yaml) | **OpenAI-compatible** local server (e.g. LM Studio); `host.docker.internal` and `extraHosts` for Linux Docker. |
| [`workspace-fs.yaml`](examples/agents/workspace-fs.yaml) | Shared **named volume** + **fsTools** (list/search/edit under workspace). |
| [`with-mcp.yaml`](examples/agents/with-mcp.yaml) | **stdio MCP** (example: npx `@modelcontextprotocol/server-everything`). |
| [`gitea-mcp.yaml`](examples/agents/gitea-mcp.yaml) | **HTTP MCP** to Gitea (`GITEA_ACCESS_TOKEN`, compose `gitea` + `gitea-mcp` with profile `mcp`). |

More notes live in [`examples/README.md`](examples/README.md).

### `apply` output: `demo` manifest

**Example command** (add `--force` if `.agents/demo` already exists):

```bash
uv run agentctl apply examples/agents/demo.yaml
```

**[`examples/agents/demo.yaml`](examples/agents/demo.yaml)** — source manifest:

```yaml
apiVersion: agentctl/v1
metadata:
  name: demo
spec:
  runtime: pydantic-ai
  model:
    type: ollama
    model_id: llama3.2
    base_url: http://host.docker.internal:11434/v1
  prompts:
    system: You are a concise demo agent for agentctl.
  deploy:
    port: 8080
    composeService: demo
```

### will generate

**Generated** `.agents/demo` **files** (Pydantic AI runtime):

```text
.agents/demo
├── compose.agent.yml
├── Dockerfile
├── manifest.resolved.yaml
└── python
    ├── pyproject.toml
    ├── README.md
    └── server.py
```

`apply` also prints a short summary, e.g. `Wrote 6 artifacts under …/.agents/demo`.

**`compose.agent.yml`** — service merged with the root `docker-compose.yml` when you `agentctl deploy demo`:

```yaml
services:
  demo:
    build:
      context: ./.agents/demo
      dockerfile: Dockerfile
    image: agentctl/demo:local
    environment:
      REDIS_URL: redis://redis:6379/0
      PORT: "8080"
      GATEWAY_URL: ${GATEWAY_URL:-http://gateway:8000}
      AGENT_HOST: demo
      AGENT_NAME: demo
      GATEWAY_HEARTBEAT_SEC: ${GATEWAY_HEARTBEAT_SEC:-45}
    ports:
      - "8080:8080"
    networks:
      - agentctl-net
    depends_on:
      - redis
```

**`python/server.py`** — Ollama-backed FastAPI app (abbreviated; full file is under `.agents/demo/python/` after `apply`):

```python
"""Generated agent runtime (pydantic-ai). Do not edit by hand — regenerate with agentctl apply."""
# ... imports: os, asyncio, httpx, FastAPI, pydantic_ai (OllamaModel, OllamaProvider), …

PORT = int(os.environ.get("PORT", "8080"))
GATEWAY_URL = os.environ.get("GATEWAY_URL", "").strip()
AGENT_NAME = os.environ.get("AGENT_NAME", "demo").strip()
AGENT_HOST = os.environ.get("AGENT_HOST", "demo").strip()
# ... REDIS_URL, GATEWAY_HEARTBEAT_SEC, placeholders for MCP / fs tools, …

async def _register_with_gateway() -> None:
    if not GATEWAY_URL:
        return
    # POST {GATEWAY_URL}/api/agents/register
    #   json={"name": AGENT_NAME, "host": AGENT_HOST, "port": PORT}
    ...

# ... _gateway_heartbeat_loop, MCP and fs tool plumbing, …

def build_agent() -> Agent[None, str]:
    return Agent(
        model=OllamaModel(
            "llama3.2",
            provider=OllamaProvider(base_url="http://host.docker.internal:11434/v1"),
        ),
        system_prompt="You are a concise demo agent for agentctl.",
    )

# ... lifespan: build_agent(), _register_with_gateway(), optional periodic heartbeat, …

app = FastAPI(title="demo", lifespan=lifespan)

# class InvokeBody: message, optional context, …

@app.get("/health")
async def health():
    return {"status": "ok", "agent": "demo"}

@app.post("/invoke")
async def invoke(body: InvokeBody):
    text = body.message
    # ... optionally append JSON from body.context to `text`
    result = await _agent.run(text)
    return {"output": result.output}
```

## Available command specs

- **`.cursor/commands/create-team.md`** — `/create-team` command that discovers the project stack, reconciles existing agents/skills, and scaffolds a specialized team plus `/team` manifest.
- **`.claude/commands/create-team.md`** — Same flow for Claude Code.
