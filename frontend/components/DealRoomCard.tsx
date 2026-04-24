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
  const href = `/deal-rooms/${dealRoom.id}`;

  return (
    <Card className="group relative flex flex-col gap-5 overflow-hidden p-5 transition-all hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-elevated">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/50 to-transparent opacity-0 transition-opacity group-hover:opacity-100"
      />

      <div className="flex items-start gap-3">
        <span
          aria-hidden="true"
          className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500/15 to-indigo-500/5 text-primary ring-1 ring-primary/15"
        >
          <Building2Icon className="h-5 w-5" />
        </span>
        <div className="min-w-0 flex-1">
          <Link
            href={href}
            className="block truncate text-base font-semibold text-foreground transition-colors hover:text-primary focus-visible:text-primary focus-visible:outline-none"
          >
            {dealRoom.name}
          </Link>
          {dealRoom.target_company ? (
            <p className="mt-0.5 truncate text-sm text-muted-foreground">
              Target ·{" "}
              <span className="text-foreground/80">
                {dealRoom.target_company}
              </span>
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
              <TrashIcon className="h-4 w-4" aria-hidden="true" />
              {deleting ? "Deleting…" : "Delete deal room"}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <div className="mt-auto flex items-center justify-between gap-2 border-t border-border/70 pt-4">
        <Badge
          variant="secondary"
          className="font-normal normal-case tracking-normal"
        >
          Created {formatRelativeTime(created)}
        </Badge>
        <Link
          href={href}
          className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-sm font-medium text-primary transition-colors hover:bg-primary/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
          aria-label={`Open ${dealRoom.name}`}
        >
          Open
          <ChevronRightIcon
            className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5"
            aria-hidden="true"
          />
        </Link>
      </div>
    </Card>
  );
}
