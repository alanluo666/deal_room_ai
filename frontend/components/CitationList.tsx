"use client";

/**
 * Citation display helpers.
 *
 * Two variants are exposed so callers can pick the right visual weight:
 *
 *   - `<CitationList>`   — full list with filename, chunk index, and snippet.
 *                          Used for the primary "Latest answer" card and the
 *                          expanded "Past questions" rows.
 *
 *   - `<CitationChips>`  — compact pill row showing filename + chunk index
 *                          only. Used inside denser surfaces like Findings
 *                          cards and chat bubbles where long source snippets
 *                          would dominate the layout.
 */

import { FileTextIcon } from "@/components/icons";
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
            <FileTextIcon
              className="h-3 w-3 text-muted-foreground"
              aria-hidden="true"
            />
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

/**
 * Compact source chips. Each chip shows filename + chunk index with a
 * truncated tooltip of the underlying snippet so users can still inspect
 * the source without expanding the whole list.
 */
export function CitationChips({ citations }: Props) {
  if (citations.length === 0) return null;
  return (
    <ul className="flex flex-wrap gap-1.5">
      {citations.map((cit, idx) => (
        <li
          key={`${cit.document_id}:${cit.chunk_index}:${idx}`}
          className="inline-flex max-w-[260px] items-center gap-1 rounded-full border border-border bg-background px-2 py-0.5 text-[11px] text-muted-foreground"
          title={cit.snippet}
        >
          <FileTextIcon
            className="h-3 w-3 shrink-0 text-muted-foreground"
            aria-hidden="true"
          />
          <span className="truncate font-medium text-foreground">
            {cit.filename}
          </span>
          <span className="shrink-0 text-muted-foreground">
            #{cit.chunk_index}
          </span>
        </li>
      ))}
    </ul>
  );
}
