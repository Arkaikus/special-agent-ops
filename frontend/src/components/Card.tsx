import { useDraggable } from "@dnd-kit/core";
import type { Card as CardT } from "../api/client";

const PRIORITY_LABEL = ["—", "Low", "Med", "High"] as const;

export function Card({
  card,
  onEdit,
}: {
  card: CardT;
  onEdit: (c: CardT) => void;
}) {
  const { attributes, listeners, setNodeRef, transform, isDragging } =
    useDraggable({
      id: card.id,
    });
  const style = transform
    ? { transform: `translate3d(${transform.x}px, ${transform.y}px, 0)` }
    : undefined;
  const pLabel =
    PRIORITY_LABEL[card.priority as 0 | 1 | 2 | 3] ?? PRIORITY_LABEL[0];
  return (
    <div
      className={`flex gap-1 rounded-md border border-[#2a3441] bg-[#0f1419] p-2 text-sm ${
        isDragging ? "opacity-85 shadow-lg" : ""
      }`}
      ref={setNodeRef}
      style={style}
    >
      <button
        type="button"
        className="cursor-grab touch-none rounded border border-transparent px-0.5 text-[#8899a6] hover:border-[#2a3441]"
        aria-label="Drag card"
        {...listeners}
        {...attributes}
      >
        ⠿
      </button>
      <button
        type="button"
        className="min-w-0 flex-1 cursor-pointer rounded px-1 text-left text-inherit"
        onClick={() => onEdit(card)}
      >
        <div className="flex flex-wrap items-center gap-1.5">
          <strong>{card.title}</strong>
          {card.priority > 0 && (
            <span className="rounded bg-sky-900/40 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-sky-300">
              {pLabel}
            </span>
          )}
          {card.team_label ? (
            <span className="rounded bg-violet-900/40 px-1.5 py-0.5 text-[10px] text-violet-200">
              {card.team_label}
            </span>
          ) : null}
          {card.agent_name ? (
            <span className="rounded bg-[#2a3441] px-1.5 py-0.5 text-[10px] text-[#8899a6]">
              @{card.agent_name}
            </span>
          ) : null}
        </div>
        {card.body && (
          <p className="mt-1.5 line-clamp-3 text-[#8899a6]">{card.body}</p>
        )}
      </button>
    </div>
  );
}
