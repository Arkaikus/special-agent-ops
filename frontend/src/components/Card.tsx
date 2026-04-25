import { useDraggable } from "@dnd-kit/core";
import type { Card as CardT } from "../api/client";

export function Card({ card }: { card: CardT }) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: card.id,
  });
  const style = transform
    ? { transform: `translate3d(${transform.x}px, ${transform.y}px, 0)` }
    : undefined;
  return (
    <div
      ref={setNodeRef}
      className={`card ${isDragging ? "dragging" : ""}`}
      style={style}
      {...listeners}
      {...attributes}
    >
      <strong>{card.title}</strong>
      {card.body && <p>{card.body}</p>}
    </div>
  );
}
