import { useDroppable } from "@dnd-kit/core";
import type { Card as CardT, Column as ColumnT } from "../api/client";
import { Card } from "./Card";

export function Column({ column }: { column: ColumnT }) {
  const { setNodeRef } = useDroppable({ id: `col-${column.id}` });
  return (
    <div
      className="min-h-[200px] rounded-lg border border-[#2a3441] bg-[#1a2332] p-3"
      ref={setNodeRef}
    >
      <h2 className="mb-3 text-xs font-medium uppercase tracking-wider text-[#8899a6]">
        {column.title}
      </h2>
      <div className="flex flex-col gap-2">
        {column.cards.map((c: CardT) => (
          <Card card={c} key={c.id} />
        ))}
      </div>
    </div>
  );
}
