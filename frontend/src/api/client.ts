const base = import.meta.env.VITE_GATEWAY_URL ?? "http://localhost:8000";

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${base}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!r.ok) {
    const t = await r.text();
    throw new Error(`${r.status} ${t}`);
  }
  if (r.status === 204) {
    return undefined as T;
  }
  const text = await r.text();
  if (!text) {
    return undefined as T;
  }
  return JSON.parse(text) as T;
}

export type Project = {
  id: number;
  name: string;
  description: string;
  default_agent: string | null;
  default_agent_port: number;
};

export type RegisteredAgent = {
  id: number;
  name: string;
  host: string;
  port: number;
  project_ids: number[];
  last_seen_at: string;
  available: boolean;
};

export type Card = {
  id: number;
  column_id: number;
  title: string;
  body: string;
  position: number;
  agent_name: string | null;
  priority: number;
  team_label: string;
};

export type Column = {
  id: number;
  title: string;
  position: number;
  cards: Card[];
};

export type Board = {
  project_id: number;
  columns: Column[];
};

/** Global registry; optional `forProjectId` limits to agents with no project links or linked to that project. */
export function listAgents(forProjectId?: number): Promise<RegisteredAgent[]> {
  const q =
    forProjectId !== undefined
      ? `?for_project_id=${encodeURIComponent(String(forProjectId))}`
      : "";
  return api<RegisteredAgent[]>(`/api/agents${q}`);
}

export function getAgent(agentId: number): Promise<RegisteredAgent> {
  return api<RegisteredAgent>(`/api/agents/${agentId}`);
}

export function addAgentToProject(
  agentId: number,
  projectId: number,
): Promise<RegisteredAgent> {
  return api<RegisteredAgent>(`/api/agents/${agentId}/projects/${projectId}`, {
    method: "POST",
  });
}

export function removeAgentFromProject(
  agentId: number,
  projectId: number,
): Promise<RegisteredAgent> {
  return api<RegisteredAgent>(`/api/agents/${agentId}/projects/${projectId}`, {
    method: "DELETE",
  });
}
