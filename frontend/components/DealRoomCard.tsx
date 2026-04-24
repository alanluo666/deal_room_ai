"use client";

import Link from "next/link";

import type { DealRoom } from "@/lib/types";
import { formatRelativeTime } from "@/lib/utils";

import {
  Building2Icon,
  ChevronRightIcon,
  MoreHorizontalIcon,
  TrashIcon,
} from "./icons";
import { Badge } from "./ui/badge";
import { Card } from "./ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";

interface Props {
  dealRoom: DealRoom;
  onDelete: (id: number) => void;
  deleting?: boolean;
}

export function DealRoomCard({ dealRoom, onDelete, deleting }: Props) {
  const created = new Date(dealRoom.created_at);

  return (
    <Card className="group relative flex flex-col gap-4 transition-colors hover:border-primary/40 hover:shadow-elevated">
      <div className="flex items-start gap-3">
        <span
          aria-hidden="true"
          className="flex h-10 w-10 items-center justify-center rounded-md bg-primary/10 text-primary"
        >
          <Building2Icon className="h-5 w-5" />
        </span>
        <div className="min-w-0 flex-1">
          <Link
            href={`/deal-rooms/${dealRoom.id}`}
            className="block truncate text-base font-semibold text-foreground hover:underline"
          >
            {dealRoom.name}
          </Link>
          {dealRoom.target_company ? (
            <p className="mt-0.5 truncate text-sm text-muted-foreground">
              Target · {dealRoom.target_company}
            </p>
          ) : (
            <p className="mt-0.5 text-sm text-muted-foreground">
              No target company set
            </p>
          )}
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger
            aria-label="Deal room actions"
            className="flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground opacity-0 transition-opacity hover:bg-accent hover:text-foreground focus-visible:opacity-100 group-hover:opacity-100 data-[state=open]:opacity-100"
          >
            <MoreHorizontalIcon className="h-4 w-4" aria-hidden="true" />
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem
              destructive
              disabled={deleting}
              onClick={() => onDelete(dealRoom.id)}
            >
              <TrashIcon className="h-4 w-4" />
              {deleting ? "Deleting…" : "Delete deal room"}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <div className="flex items-center justify-between">
        <Badge variant="secondary" className="font-normal">
          Created {formatRelativeTime(created)}
        </Badge>
        <Link
          href={`/deal-rooms/${dealRoom.id}`}
          className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-sm font-medium text-primary transition-colors hover:bg-primary/10"
        >
          Open
          <ChevronRightIcon className="h-3.5 w-3.5" />
        </Link>
      </div>
    </Card>
  );
}
