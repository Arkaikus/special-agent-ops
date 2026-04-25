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
  return r.json() as Promise<T>;
}

export type Project = {
  id: number;
  name: string;
  description: string;
  default_agent: string | null;
  default_agent_port: number;
};

export type Card = {
  id: number;
  column_id: number;
  title: string;
  body: string;
  position: number;
  agent_name: string | null;
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
