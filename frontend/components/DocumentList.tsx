"use client";

import clsx from "clsx";

import type { DealRoomDocument } from "@/lib/types";

import { Button, Card } from "./ui";

interface Props {
  documents: DealRoomDocument[];
  onDelete: (id: number) => void;
  pendingDeleteId?: number | null;
}

const STATUS_CLASSES: Record<DealRoomDocument["status"], string> = {
  ready: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200",
  processing: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200",
  pending: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
  failed: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-200",
};

function formatBytes(bytes: number) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const i = Math.min(units.length - 1, Math.floor(Math.log(bytes) / Math.log(1024)));
  return `${(bytes / Math.pow(1024, i)).toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

export function DocumentList({ documents, onDelete, pendingDeleteId }: Props) {
  if (documents.length === 0) {
    return (
      <Card>
        <p className="text-sm text-slate-600 dark:text-slate-400">
          No documents yet. Upload a PDF, DOCX, or TXT to index it for this
          deal room.
        </p>
      </Card>
    );
  }

  return (
    <Card className="p-0">
      <ul className="divide-y divide-slate-200 dark:divide-slate-800">
        {documents.map((doc) => (
          <li
            key={doc.id}
            className="flex flex-col gap-2 p-4 sm:flex-row sm:items-center sm:justify-between"
          >
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <span className="truncate text-sm font-medium">
                  {doc.filename}
                </span>
                <span
                  className={clsx(
                    "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium capitalize",
                    STATUS_CLASSES[doc.status],
                  )}
                >
                  {doc.status}
                </span>
              </div>
              <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                {formatBytes(doc.size_bytes)} ·{" "}
                {doc.chunk_count > 0
                  ? `${doc.chunk_count} chunk${doc.chunk_count === 1 ? "" : "s"}`
                  : "0 chunks"}{" "}
                · uploaded {new Date(doc.created_at).toLocaleString()}
              </div>
              {doc.status === "failed" && doc.error_message ? (
                <p className="mt-1 text-xs text-red-600 dark:text-red-400">
                  {doc.error_message}
                </p>
              ) : null}
            </div>
            <Button
              type="button"
              variant="ghost"
              className="!px-2 !py-1 text-red-600 hover:bg-red-50 dark:hover:bg-red-950"
              disabled={pendingDeleteId === doc.id}
              onClick={() => onDelete(doc.id)}
            >
              {pendingDeleteId === doc.id ? "Removing..." : "Remove"}
            </Button>
          </li>
        ))}
      </ul>
    </Card>
  );
}
