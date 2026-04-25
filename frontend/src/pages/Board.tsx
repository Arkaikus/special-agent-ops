import {
  DndContext,
  type DragEndEvent,
  PointerSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import { type FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, type Board } from "../api/client";
import { Column } from "../components/Column";

export function BoardPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const pid = Number(projectId);
  const [board, setBoard] = useState<Board | null>(null);
  const [message, setMessage] = useState("");
  const [invokeOut, setInvokeOut] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
  );

  const load = () =>
    api<Board>(`/api/projects/${pid}/board`)
      .then(setBoard)
      .catch((e) => setErr(String(e)));

  useEffect(() => {
    if (!Number.isFinite(pid)) return;
    api<Board>(`/api/projects/${pid}/board`)
      .then(setBoard)
      .catch((e) => setErr(String(e)));
  }, [pid]);

  async function onInvoke(e: FormEvent) {
    e.preventDefault();
    setErr(null);
    setInvokeOut(null);
    try {
      const r = await api<{ output: string; agent: string }>("/api/invoke", {
        method: "POST",
        body: JSON.stringify({ message, project_id: pid }),
      });
      setInvokeOut(`${r.agent}: ${r.output}`);
      await load();
    } catch (e) {
      setErr(String(e));
    }
  }

  async function onDragEnd(ev: DragEndEvent) {
    const { active, over } = ev;
    if (!over || !board) return;
    const cardId = Number(active.id);
    const colId = Number(String(over.id).replace("col-", ""));
    if (!Number.isFinite(cardId) || !Number.isFinite(colId)) return;
    const col = board.columns.find((c) => c.id === colId);
    const pos = col ? col.cards.length : 0;
    await api(`/api/cards/${cardId}`, {
      method: "PATCH",
      body: JSON.stringify({ column_id: colId, position: pos }),
    });
    await load();
  }

  if (!Number.isFinite(pid)) return <p>Invalid project</p>;
  if (!board) return <p>Loading…</p>;

  return (
    <div>
      <nav className="mb-2">
        <Link className="text-sky-300" to="/">
          ← Projects
        </Link>
      </nav>
      <h1 className="mb-4 text-2xl">Kanban</h1>
      {err && <p className="text-red-400">{err}</p>}
      <form onSubmit={onInvoke} className="mb-2 mt-2 flex flex-wrap gap-2">
        <input
          className="min-w-[180px] flex-1 rounded-md border border-[#2a3441] bg-[#1a2332] px-2.5 py-2 text-inherit"
          placeholder="Message to default agent…"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />
        <button
          className="cursor-pointer rounded-md bg-blue-600 px-4 py-2 font-semibold text-white hover:bg-blue-700"
          type="submit"
        >
          Invoke
        </button>
      </form>
      {invokeOut && (
        <pre className="mb-4 overflow-auto rounded-md border border-[#2a3441] bg-[#1a2332] p-3 text-sm">
          {invokeOut}
        </pre>
      )}
      <DndContext onDragEnd={onDragEnd} sensors={sensors}>
        <div className="mt-4 grid grid-cols-[repeat(auto-fit,minmax(220px,1fr))] gap-4">
          {board.columns.map((c) => (
            <Column column={c} key={c.id} />
          ))}
        </div>
      </DndContext>
    </div>
  );
}
