"use client";

import { Badge } from "@/components/ui/badge";
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
  return (
    <div className="rounded-md border border-border bg-muted/30 p-3 text-sm">
      {title ? (
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          {title}
        </p>
      ) : null}
      <p className="whitespace-pre-wrap text-foreground">{answer}</p>
      <CitationList citations={citations} />
      <div className="mt-3 flex flex-wrap items-center gap-1.5">
        <Badge variant="outline" className="font-normal normal-case">
          model · {model}
        </Badge>
        {typeof chunksUsed === "number" ? (
          <Badge variant="outline" className="font-normal normal-case">
            {chunksUsed} chunk{chunksUsed === 1 ? "" : "s"} used
          </Badge>
        ) : null}
      </div>
    </div>
  );
}
