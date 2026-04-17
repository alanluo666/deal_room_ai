"use client";

/**
 * FindingsPanel — Person C step 4.
 *
 * Read-only, presentational surface that renders the most recent /analyze
 * outputs (summary + risks) with their evidence citations. No network
 * calls, no mutations, no state.
 *
 * Design notes:
 * - This panel does NOT call /analyze itself. The two AnalyzeResponse
 *   values are produced by the existing analyzeMutation wired on the
 *   parent page; this panel only renders what the parent already has.
 *   Keeping it display-only means Person A's later ADK-driven findings
 *   producer can reuse the same AnalyzeResponse shape (or a sibling
 *   endpoint that returns the same shape) without a redesign here.
 * - Evidence links: we reuse the existing <AnswerCard> + <CitationList>
 *   path used by AskPanel and (now-removed) AnalyzePanel inline results,
 *   so the citation style is identical across the page. Clickable links
 *   to a document viewer are intentionally out of scope until the doc
 *   viewer lands in a later Person C step.
 */

import type { AnalyzeResponse } from "@/lib/types";

import { AnswerCard } from "./AnswerCard";
import { Card } from "./ui";

interface Props {
  latestSummary: AnalyzeResponse | null;
  latestRisks: AnalyzeResponse | null;
}

export function FindingsPanel({ latestSummary, latestRisks }: Props) {
  const hasAny = latestSummary !== null || latestRisks !== null;

  return (
    <Card className="flex flex-col gap-3">
      <div>
        <h3 className="text-sm font-semibold">Findings</h3>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Grounded summaries and flagged risks from the uploaded documents,
          with source citations.
        </p>
      </div>

      {!hasAny ? (
        <p className="text-xs text-slate-400">
          Run <em>Generate summary</em> or <em>Identify risks</em> above to
          populate findings here.
        </p>
      ) : null}

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
