# Examples

- **`agents/*.yaml`**: `agentctl apply path/to/manifest.yaml` then `agentctl deploy {name}` (see root `docker-compose.yml`).

- **LM Studio** ([`agents/lmstudio.yaml`](agents/lmstudio.yaml)): OpenAI-compatible local server. Inside Docker on Linux, use `host.docker.internal` (see `extraHosts` in the manifest) or run the model on a host IP reachable from the container.

- **Gitea MCP** ([`agents/gitea-mcp.yaml`](agents/gitea-mcp.yaml)): needs `GITEA_ACCESS_TOKEN` and the `gitea` + `gitea-mcp` services from the repo `docker-compose.yml`. After Gitea is initialized in the browser, create a personal access token and export it in your shell or `.env`.

- **Shared workspace** ([`agents/workspace-fs.yaml`](agents/workspace-fs.yaml)): named volume `agentctl-shared-ws` and filesystem tools (`ls`, `grep`, `edit`, `glob` by default; add `bash` in `fsTools.allow` if required).
