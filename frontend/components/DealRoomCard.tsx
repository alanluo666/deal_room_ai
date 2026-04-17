"use client";

import type { DealRoom } from "@/lib/types";

import { Button, Card } from "./ui";

interface Props {
  dealRoom: DealRoom;
  onDelete: (id: number) => void;
  deleting?: boolean;
}

export function DealRoomCard({ dealRoom, onDelete, deleting }: Props) {
  return (
    <Card className="flex flex-col gap-2">
      <div>
        <h3 className="text-base font-semibold">{dealRoom.name}</h3>
        {dealRoom.target_company ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Target: {dealRoom.target_company}
          </p>
        ) : null}
      </div>
      <div className="mt-2 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
        <span>Created {new Date(dealRoom.created_at).toLocaleDateString()}</span>
        <Button
          type="button"
          variant="ghost"
          onClick={() => onDelete(dealRoom.id)}
          disabled={deleting}
          className="!px-2 !py-1 text-red-600 hover:bg-red-50 dark:hover:bg-red-950"
        >
          {deleting ? "Deleting..." : "Delete"}
        </Button>
      </div>
    </Card>
  );
}
