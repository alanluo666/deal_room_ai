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
          className="rounded border border-slate-200 bg-white p-2 dark:border-slate-800 dark:bg-slate-900"
        >
          <div className="flex flex-wrap items-center gap-1 text-slate-600 dark:text-slate-300">
            <span className="font-medium">{cit.filename}</span>
            <span className="text-slate-400">· chunk #{cit.chunk_index}</span>
          </div>
          <p className="mt-1 text-slate-700 dark:text-slate-200">
            &ldquo;{cit.snippet}&rdquo;
          </p>
        </li>
      ))}
    </ol>
  );
}
