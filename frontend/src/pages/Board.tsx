import {
  DndContext,
  type DragEndEvent,
  PointerSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import { type FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, type Board, type Card as CardT } from "../api/client";
import { Column } from "../components/Column";

type ModalState =
  | { mode: "closed" }
  | { mode: "create"; columnId: number }
  | { mode: "edit"; card: CardT };

const emptyForm = {
  title: "",
  body: "",
  priority: 0,
  team_label: "",
  agent_name: "",
};

export function BoardPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const pid = Number(projectId);
  const [board, setBoard] = useState<Board | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [modal, setModal] = useState<ModalState>({ mode: "closed" });
  const [form, setForm] = useState(emptyForm);

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

  function openCreate(columnId: number) {
    setForm(emptyForm);
    setModal({ mode: "create", columnId });
  }

  function openEdit(card: CardT) {
    setForm({
      title: card.title,
      body: card.body,
      priority: card.priority,
      team_label: card.team_label,
      agent_name: card.agent_name ?? "",
    });
    setModal({ mode: "edit", card });
  }

  function closeModal() {
    setModal({ mode: "closed" });
    setForm(emptyForm);
  }

  async function saveCard(e: FormEvent) {
    e.preventDefault();
    if (modal.mode === "closed" || !board) return;
    setErr(null);
    try {
      if (modal.mode === "create") {
        const col = board.columns.find((c) => c.id === modal.columnId);
        const pos = col ? col.cards.length : 0;
        await api(`/api/projects/${pid}/cards`, {
          method: "POST",
          body: JSON.stringify({
            column_id: modal.columnId,
            title: form.title,
            body: form.body,
            position: pos,
            priority: form.priority,
            team_label: form.team_label || "",
            agent_name: form.agent_name.trim() || null,
          }),
        });
      } else {
        await api(`/api/cards/${modal.card.id}`, {
          method: "PATCH",
          body: JSON.stringify({
            title: form.title,
            body: form.body,
            priority: form.priority,
            team_label: form.team_label || "",
            agent_name: form.agent_name.trim() || null,
          }),
        });
      }
      closeModal();
      await load();
    } catch (e) {
      setErr(String(e));
    }
  }

  async function removeCard() {
    if (modal.mode !== "edit") return;
    setErr(null);
    try {
      await api(`/api/cards/${modal.card.id}`, { method: "DELETE" });
      closeModal();
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
      <nav className="mb-2 flex flex-wrap gap-3">
        <Link className="text-sky-300" to="/">
          ← Projects
        </Link>
        <Link className="text-sky-300" to={`/agents/${pid}`}>
          Agents
        </Link>
      </nav>
      <h1 className="mb-4 text-2xl">Kanban</h1>
      {err && <p className="text-red-400">{err}</p>}

      {modal.mode !== "closed" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="max-h-[90vh] w-full max-w-md overflow-y-auto rounded-lg border border-[#2a3441] bg-[#1a2332] p-5 shadow-xl">
            <h2 className="mb-4 text-lg font-semibold">
              {modal.mode === "create" ? "New card" : "Edit card"}
            </h2>
            <form onSubmit={saveCard} className="flex flex-col gap-3">
              <label className="block text-sm">
                <span className="text-[#8899a6]">Title</span>
                <input
                  required
                  className="mt-1 w-full rounded-md border border-[#2a3441] bg-[#0f1419] px-2.5 py-2 text-inherit"
                  value={form.title}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, title: e.target.value }))
                  }
                />
              </label>
              <label className="block text-sm">
                <span className="text-[#8899a6]">Description</span>
                <textarea
                  className="mt-1 min-h-[80px] w-full rounded-md border border-[#2a3441] bg-[#0f1419] px-2.5 py-2 text-inherit"
                  value={form.body}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, body: e.target.value }))
                  }
                />
              </label>
              <label className="block text-sm">
                <span className="text-[#8899a6]">Priority</span>
                <select
                  className="mt-1 w-full rounded-md border border-[#2a3441] bg-[#0f1419] px-2.5 py-2 text-inherit"
                  value={form.priority}
                  onChange={(e) =>
                    setForm((f) => ({
                      ...f,
                      priority: Number(e.target.value),
                    }))
                  }
                >
                  <option value={0}>—</option>
                  <option value={1}>Low</option>
                  <option value={2}>Med</option>
                  <option value={3}>High</option>
                </select>
              </label>
              <label className="block text-sm">
                <span className="text-[#8899a6]">Team (visual)</span>
                <input
                  className="mt-1 w-full rounded-md border border-[#2a3441] bg-[#0f1419] px-2.5 py-2 text-inherit"
                  placeholder="e.g. Platform"
                  value={form.team_label}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, team_label: e.target.value }))
                  }
                />
              </label>
              <label className="block text-sm">
                <span className="text-[#8899a6]">Assigned agent (visual)</span>
                <input
                  className="mt-1 w-full rounded-md border border-[#2a3441] bg-[#0f1419] px-2.5 py-2 text-inherit"
                  placeholder="label only"
                  value={form.agent_name}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, agent_name: e.target.value }))
                  }
                />
              </label>
              <div className="mt-2 flex flex-wrap gap-2">
                <button
                  type="submit"
                  className="cursor-pointer rounded-md bg-blue-600 px-4 py-2 font-semibold text-white hover:bg-blue-700"
                >
                  Save
                </button>
                <button
                  type="button"
                  onClick={closeModal}
                  className="cursor-pointer rounded-md border border-[#2a3441] bg-transparent px-4 py-2 text-inherit"
                >
                  Cancel
                </button>
                {modal.mode === "edit" && (
                  <button
                    type="button"
                    onClick={removeCard}
                    className="cursor-pointer rounded-md bg-red-900/60 px-4 py-2 font-semibold text-red-100 hover:bg-red-900"
                  >
                    Delete
                  </button>
                )}
              </div>
            </form>
          </div>
        </div>
      )}

      <DndContext onDragEnd={onDragEnd} sensors={sensors}>
        <div className="mt-4 grid grid-cols-[repeat(auto-fit,minmax(220px,1fr))] gap-4">
          {board.columns.map((c) => (
            <Column
              column={c}
              key={c.id}
              onAddCard={openCreate}
              onEditCard={openEdit}
            />
          ))}
        </div>
      </DndContext>
    </div>
  );
}
