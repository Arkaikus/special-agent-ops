import { useDraggable } from "@dnd-kit/core";
import type { Card as CardT } from "../api/client";

export function Card({ card }: { card: CardT }) {
  const { attributes, listeners, setNodeRef, transform, isDragging } =
    useDraggable({
      id: card.id,
    });
  const style = transform
    ? { transform: `translate3d(${transform.x}px, ${transform.y}px, 0)` }
    : undefined;
  return (
    <div
      className={`cursor-grab rounded-md border border-[#2a3441] bg-[#0f1419] p-2 text-sm ${
        isDragging ? "opacity-85 shadow-lg" : ""
      }`}
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
    >
      <strong>{card.title}</strong>
      {card.body && (
        <p className="mt-1.5 text-sm text-[#8899a6]">{card.body}</p>
      )}
    </div>
  );
}
