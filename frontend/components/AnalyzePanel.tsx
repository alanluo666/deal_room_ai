"use client";

// Results (summary + risks cards) render in FindingsPanel. This component is
// now action-only: kicks off POST /deal-rooms/{id}/analyze and surfaces the
// in-flight / error state. The route, request shape, and AnalyzeResponse
// schema it triggers are unchanged.

import type { AnalyzeResponse, AnalyzeTask } from "@/lib/types";

import { Button, Card, FieldError } from "./ui";

interface Props {
  onAnalyze: (task: AnalyzeTask) => Promise<AnalyzeResponse>;
  pendingTask: AnalyzeTask | null;
  hasDocuments: boolean;
  errorMessage: string | null;
}

export function AnalyzePanel({
  onAnalyze,
  pendingTask,
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
          Results appear in the Findings panel below; re-run anytime.
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
    </Card>
  );
}
