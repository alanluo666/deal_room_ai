"use client";

import type { Citation } from "@/lib/types";

interface Props {
  citations: Citation[];
}

export function CitationList({ citations }: Props) {
  if (citations.length === 0) {
    return null;
  }
  return (
    <ol className="mt-3 flex flex-col gap-2 text-xs">
      {citations.map((cit, idx) => (
        <li
          key={`${cit.document_id}:${cit.chunk_index}:${idx}`}
          className="rounded border border-border bg-background p-2"
        >
          <div className="flex flex-wrap items-center gap-1 text-foreground">
            <span className="font-medium">{cit.filename}</span>
            <span className="text-muted-foreground">
              · chunk #{cit.chunk_index}
            </span>
          </div>
          <p className="mt-1 text-muted-foreground">
            &ldquo;{cit.snippet}&rdquo;
          </p>
        </li>
      ))}
    </ol>
  );
}
