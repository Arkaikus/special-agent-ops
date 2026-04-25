import { useDroppable } from "@dnd-kit/core";
import type { Card as CardT, Column as ColumnT } from "../api/client";
import { Card } from "./Card";

export function Column({ column }: { column: ColumnT }) {
  const { setNodeRef } = useDroppable({ id: `col-${column.id}` });
  return (
    <div className="column" ref={setNodeRef}>
      <h2>{column.title}</h2>
      <div className="cards">
        {column.cards.map((c: CardT) => (
          <Card key={c.id} card={c} />
        ))}
      </div>
    </div>
  );
}
