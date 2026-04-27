import { useDroppable } from "@dnd-kit/core";
import type { Card as CardT, Column as ColumnT } from "../api/client";
import { Card } from "./Card";

export function Column({
  column,
  onAddCard,
  onEditCard,
}: {
  column: ColumnT;
  onAddCard: (columnId: number) => void;
  onEditCard: (card: CardT) => void;
}) {
  const { setNodeRef } = useDroppable({ id: `col-${column.id}` });
  return (
    <div
      className="min-h-[200px] rounded-lg border border-[#2a3441] bg-[#1a2332] p-3"
      ref={setNodeRef}
    >
      <div className="mb-3 flex items-center justify-between gap-2">
        <h2 className="text-xs font-medium uppercase tracking-wider text-[#8899a6]">
          {column.title}
        </h2>
        <button
          type="button"
          onClick={() => onAddCard(column.id)}
          className="cursor-pointer rounded border border-[#2a3441] bg-[#0f1419] px-2 py-1 text-xs font-medium text-sky-300 hover:border-sky-700"
        >
          + Card
        </button>
      </div>
      <div className="flex flex-col gap-2">
        {column.cards.map((c: CardT) => (
          <Card card={c} key={c.id} onEdit={onEditCard} />
        ))}
      </div>
    </div>
  );
}
