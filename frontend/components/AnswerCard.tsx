"use client";

import type { Citation } from "@/lib/types";

import { CitationList } from "./CitationList";

interface Props {
  answer: string;
  citations: Citation[];
  model: string;
  chunksUsed?: number;
  title?: string;
}

export function AnswerCard({
  answer,
  citations,
  model,
  chunksUsed,
  title,
}: Props) {
  const chunkSuffix =
    typeof chunksUsed === "number"
      ? ` · ${chunksUsed} chunk${chunksUsed === 1 ? "" : "s"} used`
      : "";

  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-sm dark:border-slate-800 dark:bg-slate-950">
      {title ? (
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
          {title}
        </p>
      ) : null}
      <p className="whitespace-pre-wrap text-slate-800 dark:text-slate-100">
        {answer}
      </p>
      <CitationList citations={citations} />
      <p className="mt-2 text-xs text-slate-400">
        model: {model}
        {chunkSuffix}
      </p>
    </div>
  );
}
