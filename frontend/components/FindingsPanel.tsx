"use client";

/**
 * FindingsPanel — executive Summary + Risks cards.
 *
 * Two responsive cards, each owning its own Generate/Regenerate button that
 * invokes the existing analyze mutation with `"summary"` or `"risks"`.
 * Results are ephemeral: nothing is persisted to the backend.
 *
 * Visual treatment mirrors the enterprise diligence mockups — a colored
 * icon tile, a subtle gradient header, a clean body area, and a compact
 * footer with source-chip citations + a model/chunks badge row.
 *
 * No API changes. If risk severity isn't structured in the response we do
 * not invent a taxonomy — we render `answer` as-is inside a typographic
 * prose block.
 */

import {
  AlertTriangleIcon,
  InfoIcon,
  Loader2Icon,
  RefreshCwIcon,
  SparklesIcon,
} from "@/components/icons";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import type {
  AnalyzeResponse,
  AnalyzeTask,
  Citation,
} from "@/lib/types";
import { cn } from "@/lib/utils";

import { CitationChips } from "./CitationList";

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
        eyebrow="Executive overview"
        description="A concise, grounded overview of the uploaded documents."
        icon={SparklesIcon}
        accent="indigo"
        hasDocuments={hasDocuments}
        pendingTask={pendingTask}
        result={latestSummary}
        onAnalyze={onAnalyze}
      />
      <FindingCard
        task="risks"
        title="Risks"
        eyebrow="Flagged concerns"
        description="Risks and red flags surfaced from the uploaded documents."
        icon={AlertTriangleIcon}
        accent="amber"
        hasDocuments={hasDocuments}
        pendingTask={pendingTask}
        result={latestRisks}
        onAnalyze={onAnalyze}
      />
    </div>
  );
}

type Accent = "indigo" | "amber";

const ACCENT_STYLES: Record<
  Accent,
  {
    tile: string;
    icon: string;
    header: string;
    rail: string;
  }
> = {
  indigo: {
    tile: "bg-primary/10 text-primary ring-1 ring-primary/15",
    icon: "text-primary",
    header:
      "bg-[linear-gradient(180deg,hsl(var(--primary)/0.06),transparent)]",
    rail: "bg-primary/70",
  },
  amber: {
    tile: "bg-amber-500/10 text-amber-600 ring-1 ring-amber-500/20 dark:text-amber-400",
    icon: "text-amber-600 dark:text-amber-400",
    header: "bg-[linear-gradient(180deg,rgba(245,158,11,0.08),transparent)]",
    rail: "bg-amber-500/70",
  },
};

interface FindingCardProps {
  task: AnalyzeTask;
  title: string;
  eyebrow: string;
  description: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  accent: Accent;
  hasDocuments: boolean;
  pendingTask: AnalyzeTask | null;
  result: AnalyzeResponse | null;
  onAnalyze: (task: AnalyzeTask) => Promise<AnalyzeResponse>;
}

function FindingCard({
  task,
  title,
  eyebrow,
  description,
  icon: Icon,
  accent,
  hasDocuments,
  pendingTask,
  result,
  onAnalyze,
}: FindingCardProps) {
  const isPending = pendingTask === task;
  const anyPending = pendingTask !== null;
  const disabled = !hasDocuments || anyPending;
  const hasResult = result !== null;
  const styles = ACCENT_STYLES[accent];

  const handleClick = async () => {
    try {
      await onAnalyze(task);
    } catch {
      /* toast handled in mutation onError */
    }
  };

  return (
    <Card className="relative flex flex-col gap-5 overflow-hidden p-0">
      <div
        aria-hidden="true"
        className={cn("absolute inset-y-0 left-0 w-0.5", styles.rail)}
      />
      <div
        className={cn(
          "flex items-start justify-between gap-3 border-b border-border px-5 pb-4 pt-5",
          styles.header,
        )}
      >
        <div className="flex min-w-0 items-start gap-3">
          <span
            aria-hidden="true"
            className={cn(
              "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg",
              styles.tile,
            )}
          >
            <Icon className="h-4 w-4" />
          </span>
          <div className="min-w-0">
            <p className="text-[11px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
              {eyebrow}
            </p>
            <h3 className="mt-0.5 text-base font-semibold tracking-tight">
              {title}
            </h3>
            <p className="mt-0.5 text-xs text-muted-foreground">
              {description}
            </p>
          </div>
        </div>
        <Button
          type="button"
          variant={hasResult ? "outline" : "primary"}
          size="sm"
          onClick={handleClick}
          disabled={disabled}
          aria-label={hasResult ? `Regenerate ${title}` : `Generate ${title}`}
          className="shrink-0"
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

      <div className="flex min-h-[120px] flex-col gap-4 px-5 pb-5">
        {result ? (
          <FindingBody answer={result.answer} citations={result.citations} />
        ) : isPending ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2Icon className="h-4 w-4 animate-spin" aria-hidden="true" />
            Analyzing the deal room…
          </div>
        ) : (
          <EmptyBody hasDocuments={hasDocuments} />
        )}

        {result ? (
          <div className="flex flex-wrap items-center gap-1.5 border-t border-border pt-3 text-xs text-muted-foreground">
            <span className="inline-flex items-center gap-1 text-[11px] font-medium uppercase tracking-wide">
              <SparklesIcon
                className={cn("h-3 w-3", styles.icon)}
                aria-hidden="true"
              />
              AI generated
            </span>
            <span aria-hidden="true" className="text-muted-foreground/50">
              ·
            </span>
            <Badge variant="outline" className="font-normal normal-case">
              model · {result.model}
            </Badge>
            <Badge variant="outline" className="font-normal normal-case">
              {result.chunks_used} chunk
              {result.chunks_used === 1 ? "" : "s"} used
            </Badge>
          </div>
        ) : null}
      </div>
    </Card>
  );
}

interface FindingBodyProps {
  answer: string;
  citations: Citation[];
}

function FindingBody({ answer, citations }: FindingBodyProps) {
  return (
    <div className="space-y-3">
      <p className="whitespace-pre-wrap text-sm leading-relaxed text-foreground">
        {answer}
      </p>
      {citations.length > 0 ? (
        <div className="space-y-1.5">
          <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
            Sources
          </p>
          <CitationChips citations={citations} />
        </div>
      ) : null}
    </div>
  );
}

function EmptyBody({ hasDocuments }: { hasDocuments: boolean }) {
  return (
    <div className="flex items-start gap-2 rounded-md border border-dashed border-border bg-muted/20 p-3 text-sm text-muted-foreground">
      <InfoIcon
        className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground"
        aria-hidden="true"
      />
      <p>
        {hasDocuments
          ? "Click Generate to produce a grounded result from the uploaded documents."
          : "Upload a document first to enable analysis."}
      </p>
    </div>
  );
}
