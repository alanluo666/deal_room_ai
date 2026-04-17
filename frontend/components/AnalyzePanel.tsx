"use client";

import type { AnalyzeResponse, AnalyzeTask } from "@/lib/types";

import { AnswerCard } from "./AnswerCard";
import { Button, Card, FieldError } from "./ui";

interface Props {
  onAnalyze: (task: AnalyzeTask) => Promise<AnalyzeResponse>;
  pendingTask: AnalyzeTask | null;
  latestSummary: AnalyzeResponse | null;
  latestRisks: AnalyzeResponse | null;
  hasDocuments: boolean;
  errorMessage: string | null;
}

export function AnalyzePanel({
  onAnalyze,
  pendingTask,
  latestSummary,
  latestRisks,
  hasDocuments,
  errorMessage,
}: Props) {
  const anyPending = pendingTask !== null;
  const disabled = !hasDocuments || anyPending;

  const run = (task: AnalyzeTask) => async () => {
    try {
      await onAnalyze(task);
    } catch {
      // Errors are surfaced via `errorMessage` from the parent mutation.
    }
  };

  return (
    <Card className="flex flex-col gap-3">
      <div>
        <h3 className="text-sm font-semibold">Analyze this deal room</h3>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Generate a grounded summary or risk list from the uploaded documents.
          Results are not saved; re-run anytime.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          variant="secondary"
          onClick={run("summary")}
          disabled={disabled}
        >
          {pendingTask === "summary" ? "Generating summary..." : "Generate summary"}
        </Button>
        <Button
          type="button"
          variant="secondary"
          onClick={run("risks")}
          disabled={disabled}
        >
          {pendingTask === "risks" ? "Identifying risks..." : "Identify risks"}
        </Button>
      </div>

      {!hasDocuments ? (
        <p className="text-xs text-slate-400">
          Upload a document first to enable analysis.
        </p>
      ) : null}

      <FieldError>{errorMessage}</FieldError>

      {latestSummary ? (
        <AnswerCard
          title="Summary"
          answer={latestSummary.answer}
          citations={latestSummary.citations}
          model={latestSummary.model}
          chunksUsed={latestSummary.chunks_used}
        />
      ) : null}

      {latestRisks ? (
        <AnswerCard
          title="Risks"
          answer={latestRisks.answer}
          citations={latestRisks.citations}
          model={latestRisks.model}
          chunksUsed={latestRisks.chunks_used}
        />
      ) : null}
    </Card>
  );
}
