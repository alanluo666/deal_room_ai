"use client";

import { useState } from "react";

import type { QuestionRead } from "@/lib/types";

import { CitationList } from "./CitationList";
import { Card } from "./ui";

interface Props {
  questions: QuestionRead[];
}

export function QuestionHistory({ questions }: Props) {
  const [expanded, setExpanded] = useState<Record<number, boolean>>({});

  if (questions.length === 0) {
    return (
      <Card>
        <p className="text-sm text-slate-600 dark:text-slate-400">
          No previous questions yet. Ask one above to get started.
        </p>
      </Card>
    );
  }

  return (
    <Card className="p-0">
      <div className="border-b border-slate-200 p-4 dark:border-slate-800">
        <h3 className="text-sm font-semibold">History</h3>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Previous questions and answers in this deal room.
        </p>
      </div>
      <ul className="divide-y divide-slate-200 dark:divide-slate-800">
        {questions.map((q) => {
          const isOpen = !!expanded[q.id];
          return (
            <li key={q.id} className="p-4">
              <button
                type="button"
                className="flex w-full items-start justify-between gap-3 text-left"
                onClick={() =>
                  setExpanded((prev) => ({ ...prev, [q.id]: !prev[q.id] }))
                }
              >
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{q.question}</p>
                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                    {new Date(q.created_at).toLocaleString()} ·{" "}
                    {q.citations.length}{" "}
                    {q.citations.length === 1 ? "citation" : "citations"}
                  </p>
                </div>
                <span className="text-xs text-slate-400">
                  {isOpen ? "Hide" : "Show"}
                </span>
              </button>
              {isOpen ? (
                <div className="mt-3 rounded-md bg-slate-50 p-3 text-sm dark:bg-slate-950">
                  <p className="whitespace-pre-wrap text-slate-800 dark:text-slate-100">
                    {q.answer}
                  </p>
                  <CitationList citations={q.citations} />
                </div>
              ) : null}
            </li>
          );
        })}
      </ul>
    </Card>
  );
}
