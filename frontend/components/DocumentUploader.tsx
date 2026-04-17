"use client";

import { useRef, useState } from "react";

import { Button, Card, FieldError } from "./ui";

const ACCEPT =
  "application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain";

interface Props {
  onUpload: (file: File) => Promise<void>;
  isUploading: boolean;
}

export function DocumentUploader({ onUpload, isUploading }: Props) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reset = () => {
    setFile(null);
    if (inputRef.current) inputRef.current.value = "";
  };

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
      <form className="flex flex-col gap-3" onSubmit={handleSubmit}>
        <div>
          <h3 className="text-sm font-semibold">Add a document</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            PDF, DOCX, or TXT. Stored locally and indexed into this deal
            room&rsquo;s vector store.
          </p>
        </div>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          className="block w-full text-sm text-slate-700 file:mr-3 file:rounded-md file:border file:border-slate-300 file:bg-white file:px-3 file:py-2 file:text-sm file:font-medium file:text-slate-700 hover:file:bg-slate-50 dark:text-slate-200 dark:file:border-slate-700 dark:file:bg-slate-900 dark:file:text-slate-200"
          onChange={(event) => {
            setError(null);
            setFile(event.target.files?.[0] ?? null);
          }}
          disabled={isUploading}
        />
        <FieldError>{error}</FieldError>
        <div className="flex items-center justify-end gap-2">
          {file ? (
            <span className="text-xs text-slate-500 dark:text-slate-400">
              Selected: {file.name}
            </span>
          ) : null}
          <Button type="submit" disabled={!file || isUploading}>
            {isUploading ? "Uploading..." : "Upload"}
          </Button>
        </div>
      </form>
    </Card>
  );
}
