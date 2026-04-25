import { type FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type Project } from "../api/client";

export function Projects() {
  const [items, setItems] = useState<Project[]>([]);
  const [name, setName] = useState("");
  const [agent, setAgent] = useState("");
  const [err, setErr] = useState<string | null>(null);

  const load = () =>
    api<Project[]>("/api/projects")
      .then(setItems)
      .catch((e) => setErr(String(e)));

  useEffect(() => {
    api<Project[]>("/api/projects")
      .then(setItems)
      .catch((e) => setErr(String(e)));
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
    <div>
      <h1 className="mb-4 text-2xl">Projects</h1>
      {err && <p className="text-red-400">{err}</p>}
      <form className="mb-4 flex flex-wrap gap-2" onSubmit={onCreate}>
        <input
          className="min-w-[180px] flex-1 rounded-md border border-[#2a3441] bg-[#1a2332] px-2.5 py-2 text-inherit"
          placeholder="Project name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <input
          className="min-w-[180px] flex-1 rounded-md border border-[#2a3441] bg-[#1a2332] px-2.5 py-2 text-inherit"
          placeholder="Default agent service name (optional)"
          value={agent}
          onChange={(e) => setAgent(e.target.value)}
        />
        <button
          className="cursor-pointer rounded-md bg-blue-600 px-4 py-2 font-semibold text-white hover:bg-blue-700"
          type="submit"
        >
          Create
        </button>
      </form>
      <ul className="list-none p-0">
        {items.map((p) => (
          <li className="border-b border-[#2a3441] py-2" key={p.id}>
            <Link
              className="text-sky-300 no-underline hover:underline"
              to={`/board/${p.id}`}
            >
              {p.name}
            </Link>
            {p.default_agent && (
              <span className="text-sm text-[#8899a6]">
                {" "}
                — agent: {p.default_agent}
              </span>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
