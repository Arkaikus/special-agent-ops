import { type FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, getAgent, type RegisteredAgent } from "../api/client";

type InvokeResponse = { output: string; agent: string };

type ChatLine = { id: string; role: "user" | "assistant"; text: string };

export function AgentChatPage() {
  const { projectId, agentId } = useParams<{
    projectId: string;
    agentId: string;
  }>();
  const pid = Number(projectId);
  const aid = Number(agentId);
  const [agent, setAgent] = useState<RegisteredAgent | null>(null);
  const [lines, setLines] = useState<ChatLine[]>([]);
  const [input, setInput] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!Number.isFinite(aid)) return;
    setErr(null);
    getAgent(aid)
      .then(setAgent)
      .catch((e) => setErr(String(e)));
  }, [aid]);

  async function onSend(e: FormEvent) {
    e.preventDefault();
    if (!input.trim() || !Number.isFinite(pid) || !Number.isFinite(aid)) return;
    setErr(null);
    setLoading(true);
    const msg = input.trim();
    setInput("");
    const userLine: ChatLine = {
      id: crypto.randomUUID(),
      role: "user",
      text: msg,
    };
    setLines((prev) => [...prev, userLine]);
    try {
      const r = await api<InvokeResponse>("/api/invoke", {
        method: "POST",
        body: JSON.stringify({
          message: msg,
          project_id: pid,
          registered_agent_id: aid,
        }),
      });
      setLines((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          text: r.output,
        },
      ]);
    } catch (e) {
      setErr(String(e));
      setLines((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          text: "(request failed — see error above)",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  if (!Number.isFinite(pid) || !Number.isFinite(aid)) {
    return <p>Invalid project or agent</p>;
  }

  return (
    <div>
      <nav className="mb-2 flex flex-wrap items-center gap-3">
        <Link className="text-sky-300" to={`/board/${pid}`}>
          ← Board
        </Link>
        <Link className="text-sky-300" to={`/agents/${pid}`}>
          Agents
        </Link>
      </nav>
      <h1 className="mb-1 text-2xl">Chat</h1>
      {agent && (
        <p className="mb-4 text-sm text-[#8899a6]">
          <span className="font-medium text-[#e8eaed]">{agent.name}</span>
          {" · "}
          {agent.host}:{agent.port}
          {agent.available ? (
            <span className="ml-2 rounded bg-emerald-900/50 px-2 py-0.5 text-emerald-300">
              online
            </span>
          ) : (
            <span className="ml-2 rounded bg-amber-900/50 px-2 py-0.5 text-amber-200">
              offline
            </span>
          )}
        </p>
      )}
      {err && <p className="mb-2 text-red-400">{err}</p>}
      <div className="mb-4 max-h-[50vh] space-y-3 overflow-y-auto rounded-md border border-[#2a3441] bg-[#1a2332] p-3">
        {lines.length === 0 && (
          <p className="text-sm text-[#8899a6]">
            Send a message to this agent.
          </p>
        )}
        {lines.map((line) => (
          <div
            key={line.id}
            className={`rounded-md px-3 py-2 text-sm ${
              line.role === "user"
                ? "ml-8 bg-[#0f1419] text-[#e8eaed]"
                : "mr-8 border border-[#2a3441] bg-[#0f1419]/80 text-[#8899a6]"
            }`}
          >
            {line.text}
          </div>
        ))}
      </div>
      <form onSubmit={onSend} className="flex flex-wrap gap-2">
        <input
          className="min-w-[200px] flex-1 rounded-md border border-[#2a3441] bg-[#1a2332] px-2.5 py-2 text-inherit"
          placeholder="Message…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="cursor-pointer rounded-md bg-blue-600 px-4 py-2 font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}
