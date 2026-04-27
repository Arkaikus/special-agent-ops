import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  addAgentToProject,
  api,
  listAgents,
  type Project,
  type RegisteredAgent,
  removeAgentFromProject,
} from "../api/client";

export function AgentsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const pid = Number(projectId);
  const [agents, setAgents] = useState<RegisteredAgent[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api<Project[]>("/api/projects")
      .then(setProjects)
      .catch((e) => setErr(String(e)));
  }, []);

  useEffect(() => {
    listAgents()
      .then(setAgents)
      .catch((e) => setErr(String(e)));
  }, []);

  function projectLabel(id: number) {
    return projects.find((p) => p.id === id)?.name ?? `Project #${id}`;
  }

  async function linkToProject(agentId: number) {
    if (!Number.isFinite(pid)) return;
    setErr(null);
    try {
      const a = await addAgentToProject(agentId, pid);
      setAgents((prev) => prev.map((x) => (x.id === a.id ? a : x)));
    } catch (e) {
      setErr(String(e));
    }
  }

  async function unlinkFromProject(agentId: number) {
    if (!Number.isFinite(pid)) return;
    setErr(null);
    try {
      const a = await removeAgentFromProject(agentId, pid);
      setAgents((prev) => prev.map((x) => (x.id === a.id ? a : x)));
    } catch (e) {
      setErr(String(e));
    }
  }

  if (!Number.isFinite(pid)) return <p>Invalid project</p>;

  return (
    <div>
      <nav className="mb-2 flex flex-wrap gap-3">
        <Link className="text-sky-300" to="/">
          ← Projects
        </Link>
        <Link className="text-sky-300" to={`/board/${pid}`}>
          Board
        </Link>
      </nav>
      <h1 className="mb-4 text-2xl">Registered agents</h1>
      {err && <p className="text-red-400">{err}</p>}
      <p className="mb-4 text-sm text-[#8899a6]">
        Agents register globally when{" "}
        <code className="text-sky-300/90">GATEWAY_URL</code> is set. Associate
        an agent with one or more projects here; that does not affect
        registration. When you open chat from a project, the gateway includes{" "}
        <code className="text-sky-300/90">project_id</code> in invoke{" "}
        <code className="text-sky-300/90">context</code>.
      </p>
      <ul className="list-none space-y-2 p-0">
        {agents.map((a) => {
          const linkedHere = a.project_ids.includes(pid);
          return (
            <li
              key={a.id}
              className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-[#2a3441] bg-[#1a2332] px-4 py-3"
            >
              <div className="min-w-0 flex-1">
                <span className="font-medium">{a.name}</span>
                <span className="ml-2 text-sm text-[#8899a6]">
                  {a.host}:{a.port}
                </span>
                {a.available ? (
                  <span className="ml-2 rounded bg-emerald-900/50 px-2 py-0.5 text-xs text-emerald-300">
                    available
                  </span>
                ) : (
                  <span className="ml-2 rounded bg-amber-900/50 px-2 py-0.5 text-xs text-amber-200">
                    unavailable
                  </span>
                )}
                {a.project_ids.length > 0 && (
                  <p className="mt-1.5 text-xs text-[#8899a6]">
                    Projects:{" "}
                    <span className="text-[#e8eaed]">
                      {a.project_ids.map(projectLabel).join(", ")}
                    </span>
                  </p>
                )}
              </div>
              <div className="flex flex-wrap items-center gap-2">
                {!linkedHere ? (
                  <button
                    type="button"
                    onClick={() => linkToProject(a.id)}
                    className="cursor-pointer rounded-md border border-[#2a3441] bg-[#0f1419] px-3 py-1.5 text-xs font-medium text-sky-300 hover:border-sky-700"
                  >
                    Add to this project
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={() => unlinkFromProject(a.id)}
                    className="cursor-pointer rounded-md border border-[#2a3441] bg-[#0f1419] px-3 py-1.5 text-xs font-medium text-[#8899a6] hover:border-amber-800 hover:text-amber-200"
                  >
                    Remove from this project
                  </button>
                )}
                <Link
                  className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-semibold text-white no-underline hover:bg-blue-700"
                  to={`/chat/${pid}/${a.id}`}
                >
                  Open chat
                </Link>
              </div>
            </li>
          );
        })}
      </ul>
      {agents.length === 0 && !err && (
        <p className="text-[#8899a6]">No agents registered yet.</p>
      )}
    </div>
  );
}
