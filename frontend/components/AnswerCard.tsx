"use client";

import { SparklesIcon } from "@/components/icons";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
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
    <Card className="relative flex flex-col gap-3 overflow-hidden p-0">
      <div
        aria-hidden="true"
        className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/60 to-transparent"
      />
      <div className="flex items-start gap-3 px-5 pt-5">
        <span
          aria-hidden="true"
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary"
        >
          <SparklesIcon className="h-4 w-4" />
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-[11px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
            {title ?? "Answer"}
          </p>
          <p className="mt-1 whitespace-pre-wrap text-sm leading-relaxed text-foreground">
            {answer}
          </p>
        </div>
      </div>

      {citations.length > 0 ? (
        <div className="px-5">
          <CitationList citations={citations} />
        </div>
      ) : null}

      <div className="flex flex-wrap items-center gap-1.5 border-t border-border bg-muted/20 px-5 py-3 text-xs text-muted-foreground">
        <span className="text-[11px] font-medium uppercase tracking-wide">
          AI generated
        </span>
        <span aria-hidden="true" className="text-muted-foreground/50">
          ·
        </span>
        <Badge variant="outline" className="font-normal normal-case">
          model · {model}
        </Badge>
        {typeof chunksUsed === "number" ? (
          <Badge variant="outline" className="font-normal normal-case">
            {chunksUsed} chunk{chunksUsed === 1 ? "" : "s"} used
          </Badge>
        ) : null}
      </div>
    </Card>
  );
}
