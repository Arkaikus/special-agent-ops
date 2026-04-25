import {
  DndContext,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import { useEffect, useState } from "react";
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

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 6 } }));

  const load = () =>
    api<Board>(`/api/projects/${pid}/board`).then(setBoard).catch((e) => setErr(String(e)));

  useEffect(() => {
    if (Number.isFinite(pid)) load();
  }, [pid]);

  async function onInvoke(e: React.FormEvent) {
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
    <div className="page">
      <nav className="nav">
        <Link to="/">← Projects</Link>
      </nav>
      <h1>Kanban</h1>
      {err && <p className="error">{err}</p>}
      <form onSubmit={onInvoke} className="row invoke">
        <input
          placeholder="Message to default agent…"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />
        <button type="submit">Invoke</button>
      </form>
      {invokeOut && <pre className="out">{invokeOut}</pre>}
      <DndContext sensors={sensors} onDragEnd={onDragEnd}>
        <div className="kanban">
          {board.columns.map((c) => (
            <Column key={c.id} column={c} />
          ))}
        </div>
      </DndContext>
    </div>
  );
}
