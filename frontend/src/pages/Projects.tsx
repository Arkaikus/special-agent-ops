import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { api, type Project } from "../api/client";

export function Projects() {
  const [items, setItems] = useState<Project[]>([]);
  const [name, setName] = useState("");
  const [agent, setAgent] = useState("");
  const [err, setErr] = useState<string | null>(null);

  const load = () =>
    api<Project[]>("/api/projects").then(setItems).catch((e) => setErr(String(e)));

  useEffect(() => {
    load();
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    setErr(null);
    await api<Project>("/api/projects", {
      method: "POST",
      body: JSON.stringify({
        name,
        description: "",
        default_agent: agent || null,
        default_agent_port: 8080,
      }),
    });
    setName("");
    setAgent("");
    await load();
  }

  return (
    <div className="page">
      <h1>Projects</h1>
      {err && <p className="error">{err}</p>}
      <form onSubmit={onCreate} className="row">
        <input
          placeholder="Project name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <input
          placeholder="Default agent service name (optional)"
          value={agent}
          onChange={(e) => setAgent(e.target.value)}
        />
        <button type="submit">Create</button>
      </form>
      <ul className="list">
        {items.map((p) => (
          <li key={p.id}>
            <Link to={`/board/${p.id}`}>{p.name}</Link>
            {p.default_agent && (
              <span className="muted"> — agent: {p.default_agent}</span>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
