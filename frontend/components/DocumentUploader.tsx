"use client";

import {
  useCallback,
  useRef,
  useState,
  type DragEvent,
  type KeyboardEvent,
} from "react";

import { FileIcon, Loader2Icon, UploadIcon, XIcon } from "@/components/icons";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { FieldError } from "@/components/ui/field-error";
import { cn } from "@/lib/utils";

const ACCEPT =
  "application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain";

interface Props {
  onUpload: (file: File) => Promise<void>;
  isUploading: boolean;
}

function formatBytes(bytes: number) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const i = Math.min(
    units.length - 1,
    Math.floor(Math.log(bytes) / Math.log(1024)),
  );
  return `${(bytes / Math.pow(1024, i)).toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

export function DocumentUploader({ onUpload, isUploading }: Props) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const reset = useCallback(() => {
    setFile(null);
    if (inputRef.current) inputRef.current.value = "";
  }, []);

  const acceptFile = useCallback((next: File | undefined | null) => {
    if (!next) return;
    setError(null);
    setFile(next);
  }, []);

  const openPicker = useCallback(() => {
    if (isUploading) return;
    inputRef.current?.click();
  }, [isUploading]);

  const handleKeyDown = useCallback(
    (event: KeyboardEvent<HTMLDivElement>) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openPicker();
      }
    },
    [openPicker],
  );

  const handleDragOver = useCallback(
    (event: DragEvent<HTMLDivElement>) => {
      if (isUploading) return;
      event.preventDefault();
      setIsDragging(true);
    },
    [isUploading],
  );

  const handleDragLeave = useCallback(
    (event: DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      setIsDragging(false);
    },
    [],
  );

  const handleDrop = useCallback(
    (event: DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      setIsDragging(false);
      if (isUploading) return;
      const dropped = event.dataTransfer.files?.[0];
      acceptFile(dropped);
    },
    [acceptFile, isUploading],
  );

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    if (!file) {
      setError("Choose a file first.");
      return;
    }
    try {
      await onUpload(file);
      reset();
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Upload failed. Try again.";
      setError(message);
    }
  };

  return (
    <Card>
      <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
        <div>
          <h3 className="text-sm font-semibold">Add a document</h3>
          <p className="text-xs text-muted-foreground">
            PDF, DOCX, or TXT. Stored locally and indexed into this deal
            room&rsquo;s vector store.
          </p>
        </div>

        <div
          role="button"
          tabIndex={isUploading ? -1 : 0}
          aria-label="Upload a document"
          aria-disabled={isUploading}
          onClick={openPicker}
          onKeyDown={handleKeyDown}
          onDragOver={handleDragOver}
          onDragEnter={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={cn(
            "group relative flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed px-6 py-10 text-center transition-colors",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
            isDragging
              ? "border-primary bg-primary/5"
              : "border-border bg-muted/30 hover:border-primary/60 hover:bg-muted/50",
            isUploading && "cursor-not-allowed opacity-80",
          )}
        >
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPT}
            className="sr-only"
            onChange={(event) => acceptFile(event.target.files?.[0])}
            disabled={isUploading}
          />
          <span
            className={cn(
              "flex h-11 w-11 items-center justify-center rounded-full transition-colors",
              isDragging
                ? "bg-primary/15 text-primary"
                : "bg-background text-muted-foreground group-hover:text-foreground",
            )}
            aria-hidden="true"
          >
            {isUploading ? (
              <Loader2Icon className="h-5 w-5 animate-spin" />
            ) : (
              <UploadIcon className="h-5 w-5" />
            )}
          </span>
          <div className="space-y-1">
            <p className="text-sm font-medium text-foreground">
              {isUploading
                ? "Uploading…"
                : "Drag & drop or click to browse"}
            </p>
            <p className="text-xs text-muted-foreground">
              PDF, DOCX, or TXT up to your server limit.
            </p>
          </div>

          {isUploading ? (
            <div
              className="absolute inset-x-0 bottom-0 h-0.5 overflow-hidden rounded-b-lg bg-muted"
              aria-hidden="true"
            >
              <div className="h-full w-1/3 animate-indeterminate bg-primary" />
            </div>
          ) : null}
        </div>

        {file ? (
          <div className="flex items-center justify-between gap-3 rounded-md border border-border bg-muted/30 px-3 py-2">
            <div className="flex min-w-0 items-center gap-2">
              <FileIcon
                className="h-4 w-4 shrink-0 text-muted-foreground"
                aria-hidden="true"
              />
              <div className="min-w-0">
                <div className="truncate text-sm font-medium">{file.name}</div>
                <div className="text-xs text-muted-foreground">
                  {formatBytes(file.size)}
                </div>
              </div>
            </div>
            <button
              type="button"
              onClick={reset}
              disabled={isUploading}
              aria-label="Remove selected file"
              className="inline-flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground hover:bg-accent hover:text-foreground disabled:opacity-50"
            >
              <XIcon className="h-3.5 w-3.5" aria-hidden="true" />
            </button>
          </div>
        ) : null}

        <FieldError>{error}</FieldError>

        <div className="flex items-center justify-end gap-2">
          <Button type="submit" disabled={!file || isUploading}>
            {isUploading ? (
              <>
                <Loader2Icon className="h-4 w-4 animate-spin" aria-hidden="true" />
                Uploading…
              </>
            ) : (
              <>
                <UploadIcon className="h-4 w-4" aria-hidden="true" />
                Upload
              </>
            )}
          </Button>
        </div>
      </form>
    </Card>
  );
}
