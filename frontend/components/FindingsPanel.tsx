"use client";

/**
 * FindingsPanel — Person C, merged Analyze + Findings surface.
 *
 * A single polished panel with two responsive cards (Summary, Risks). Each
 * card owns its own Generate / Regenerate button that calls the existing
 * analyze mutation with `"summary"` or `"risks"`. Results live in component
 * state on the parent page (ephemeral, non-persisted) — same contract as
 * before; no API changes.
 *
 * The older action-only `AnalyzePanel` is no longer rendered by the page,
 * but the file is kept in-tree to avoid breaking any lingering imports.
 */

import { Loader2Icon, RefreshCwIcon, SparklesIcon } from "@/components/icons";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import type { AnalyzeResponse, AnalyzeTask } from "@/lib/types";

import { CitationList } from "./CitationList";

interface Props {
  hasDocuments: boolean;
  pendingTask: AnalyzeTask | null;
  latestSummary: AnalyzeResponse | null;
  latestRisks: AnalyzeResponse | null;
  onAnalyze: (task: AnalyzeTask) => Promise<AnalyzeResponse>;
}

export function FindingsPanel({
  hasDocuments,
  pendingTask,
  latestSummary,
  latestRisks,
  onAnalyze,
}: Props) {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <FindingCard
        task="summary"
        title="Summary"
        description="A concise, grounded overview of the uploaded documents."
        hasDocuments={hasDocuments}
        pendingTask={pendingTask}
        result={latestSummary}
        onAnalyze={onAnalyze}
      />
      <FindingCard
        task="risks"
        title="Risks"
        description="Flagged concerns and red flags surfaced from the documents."
        hasDocuments={hasDocuments}
        pendingTask={pendingTask}
        result={latestRisks}
        onAnalyze={onAnalyze}
      />
    </div>
  );
}

interface FindingCardProps {
  task: AnalyzeTask;
  title: string;
  description: string;
  hasDocuments: boolean;
  pendingTask: AnalyzeTask | null;
  result: AnalyzeResponse | null;
  onAnalyze: (task: AnalyzeTask) => Promise<AnalyzeResponse>;
}

function FindingCard({
  task,
  title,
  description,
  hasDocuments,
  pendingTask,
  result,
  onAnalyze,
}: FindingCardProps) {
  const isPending = pendingTask === task;
  const anyPending = pendingTask !== null;
  const disabled = !hasDocuments || anyPending;
  const hasResult = result !== null;

  const handleClick = async () => {
    try {
      await onAnalyze(task);
    } catch {
      /* toast handled in mutation onError */
    }
  };

  return (
    <Card className="flex flex-col gap-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <SparklesIcon
              className="h-4 w-4 text-primary"
              aria-hidden="true"
            />
            <h3 className="text-sm font-semibold">{title}</h3>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">{description}</p>
        </div>
        <Button
          type="button"
          variant={hasResult ? "outline" : "primary"}
          size="sm"
          onClick={handleClick}
          disabled={disabled}
          aria-label={
            hasResult ? `Regenerate ${title}` : `Generate ${title}`
          }
        >
          {isPending ? (
            <>
              <Loader2Icon
                className="h-3.5 w-3.5 animate-spin"
                aria-hidden="true"
              />
              {hasResult ? "Regenerating…" : "Generating…"}
            </>
          ) : hasResult ? (
            <>
              <RefreshCwIcon className="h-3.5 w-3.5" aria-hidden="true" />
              Regenerate
            </>
          ) : (
            <>
              <SparklesIcon className="h-3.5 w-3.5" aria-hidden="true" />
              Generate
            </>
          )}
        </Button>
      </div>

      <div className="min-h-[80px]">
        {result ? (
          <div className="space-y-3">
            <p className="whitespace-pre-wrap text-sm text-foreground">
              {result.answer}
            </p>
            <CitationList citations={result.citations} />
            <div className="flex flex-wrap items-center gap-2 pt-1 text-xs text-muted-foreground">
              <Badge variant="outline" className="font-normal normal-case">
                model · {result.model}
              </Badge>
              <Badge variant="outline" className="font-normal normal-case">
                {result.chunks_used} chunk
                {result.chunks_used === 1 ? "" : "s"} used
              </Badge>
            </div>
          </div>
        ) : isPending ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2Icon className="h-4 w-4 animate-spin" aria-hidden="true" />
            {hasResult ? "Regenerating…" : "Generating…"}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            {hasDocuments
              ? "Nothing generated yet. Click Generate to produce a grounded result."
              : "Upload a document first to enable analysis."}
          </p>
        )}
      </div>
    </Card>
  );
}
