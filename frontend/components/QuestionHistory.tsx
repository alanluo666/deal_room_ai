"use client";

import { useState } from "react";

import { ChevronDownIcon, ChevronRightIcon, HistoryIcon } from "@/components/icons";
import { EmptyState } from "@/components/shell/EmptyState";
import { Card } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import type { QuestionRead } from "@/lib/types";
import { formatRelativeTime } from "@/lib/utils";

import { CitationList } from "./CitationList";

interface Props {
  questions: QuestionRead[];
}

export function QuestionHistory({ questions }: Props) {
  const [expanded, setExpanded] = useState<Record<number, boolean>>({});

  if (questions.length === 0) {
    return (
      <EmptyState
        icon={HistoryIcon}
        title="No past questions yet"
        description="Your previous Ask queries and answers will show up here."
      />
    );
  }

  return (
    <Card className="p-0">
      <div className="flex items-center gap-2 px-5 py-4">
        <HistoryIcon
          className="h-4 w-4 text-muted-foreground"
          aria-hidden="true"
        />
        <div>
          <h3 className="text-sm font-semibold">Past questions</h3>
          <p className="text-xs text-muted-foreground">
            Previous questions and answers in this deal room.
          </p>
        </div>
      </div>
      <Separator />
      <ul className="divide-y divide-border">
        {questions.map((q) => {
          const isOpen = !!expanded[q.id];
          const Chevron = isOpen ? ChevronDownIcon : ChevronRightIcon;
          return (
            <li key={q.id}>
              <button
                type="button"
                className="flex w-full items-start gap-3 px-5 py-3 text-left hover:bg-muted/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
                aria-expanded={isOpen}
                onClick={() =>
                  setExpanded((prev) => ({ ...prev, [q.id]: !prev[q.id] }))
                }
              >
                <Chevron
                  className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground"
                  aria-hidden="true"
                />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{q.question}</p>
                  <p
                    className="mt-0.5 text-xs text-muted-foreground"
                    title={new Date(q.created_at).toLocaleString()}
                  >
                    {formatRelativeTime(new Date(q.created_at))} ·{" "}
                    {q.citations.length}{" "}
                    {q.citations.length === 1 ? "citation" : "citations"}
                  </p>
                </div>
              </button>
              {isOpen ? (
                <div className="px-5 pb-4">
                  <div className="rounded-md border border-border bg-muted/30 p-3 text-sm">
                    <p className="whitespace-pre-wrap text-foreground">
                      {q.answer}
                    </p>
                    <CitationList citations={q.citations} />
                  </div>
                </div>
              ) : null}
            </li>
          );
        })}
      </ul>
    </Card>
  );
}
