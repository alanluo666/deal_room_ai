"use client";

import { FileIcon, InboxIcon, Loader2Icon, TrashIcon } from "@/components/icons";
import { EmptyState } from "@/components/shell/EmptyState";
import { Badge, type BadgeVariant } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { DealRoomDocument, DocumentStatus } from "@/lib/types";
import { cn, formatRelativeTime } from "@/lib/utils";

interface Props {
  documents: DealRoomDocument[];
  onDelete: (id: number) => void;
  pendingDeleteId?: number | null;
}

const STATUS_BADGE: Record<
  DocumentStatus,
  { variant: BadgeVariant; label: string }
> = {
  ready: { variant: "success", label: "Ready" },
  processing: { variant: "warning", label: "Processing" },
  pending: { variant: "secondary", label: "Pending" },
  failed: { variant: "destructive", label: "Failed" },
};

function formatBytes(bytes: number) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const i = Math.min(
    units.length - 1,
    Math.floor(Math.log(bytes) / Math.log(1024)),
  );
  return `${(bytes / Math.pow(1024, i)).toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

export function DocumentList({ documents, onDelete, pendingDeleteId }: Props) {
  if (documents.length === 0) {
    return (
      <EmptyState
        icon={InboxIcon}
        title="No documents yet"
        description="Upload a PDF, DOCX, or TXT to index it for this deal room."
      />
    );
  }

  return (
    <Card className="overflow-hidden p-0">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead className="w-[40%]">Name</TableHead>
            <TableHead className="w-[110px]">Status</TableHead>
            <TableHead className="w-[100px]">Size</TableHead>
            <TableHead className="w-[90px]">Chunks</TableHead>
            <TableHead className="w-[160px]">Uploaded</TableHead>
            <TableHead className="w-[90px] text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {documents.map((doc) => {
            const badge = STATUS_BADGE[doc.status];
            const isDeleting = pendingDeleteId === doc.id;
            const isBusy =
              doc.status === "pending" || doc.status === "processing";
            return (
              <TableRow key={doc.id}>
                <TableCell>
                  <div className="flex min-w-0 items-center gap-2">
                    <FileIcon
                      className="h-4 w-4 shrink-0 text-muted-foreground"
                      aria-hidden="true"
                    />
                    <div className="min-w-0">
                      <div className="truncate font-medium text-foreground">
                        {doc.filename}
                      </div>
                      {doc.status === "failed" && doc.error_message ? (
                        <div className="mt-0.5 truncate text-xs text-destructive">
                          {doc.error_message}
                        </div>
                      ) : null}
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge
                    variant={badge.variant}
                    className={cn(
                      "font-normal normal-case",
                      isBusy && "animate-pulse-soft",
                    )}
                  >
                    {isBusy ? (
                      <Loader2Icon
                        className="h-3 w-3 animate-spin"
                        aria-hidden="true"
                      />
                    ) : null}
                    {badge.label}
                  </Badge>
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {formatBytes(doc.size_bytes)}
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {doc.chunk_count}
                </TableCell>
                <TableCell
                  className="text-muted-foreground"
                  title={new Date(doc.created_at).toLocaleString()}
                >
                  {formatRelativeTime(new Date(doc.created_at))}
                </TableCell>
                <TableCell className="text-right">
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="text-destructive hover:bg-destructive/10 hover:text-destructive"
                    aria-label={`Remove ${doc.filename}`}
                    disabled={isDeleting}
                    onClick={() => onDelete(doc.id)}
                  >
                    {isDeleting ? (
                      <Loader2Icon
                        className="h-4 w-4 animate-spin"
                        aria-hidden="true"
                      />
                    ) : (
                      <TrashIcon className="h-4 w-4" aria-hidden="true" />
                    )}
                    <span className="sr-only">Remove document</span>
                  </Button>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </Card>
  );
}
