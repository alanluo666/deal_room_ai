"use client";

import { useState } from "react";

import type { AskResponse } from "@/lib/types";

import { AnswerCard } from "./AnswerCard";
import { Button, Card, FieldError } from "./ui";

interface Props {
  onAsk: (question: string) => Promise<AskResponse>;
  isAsking: boolean;
  latestAnswer: AskResponse | null;
  hasDocuments: boolean;
}

export function AskPanel({ onAsk, isAsking, latestAnswer, hasDocuments }: Props) {
  const [question, setQuestion] = useState("");
  const [error, setError] = useState<string | null>(null);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    const trimmed = question.trim();
    if (!trimmed) {
      setError("Enter a question first.");
      return;
    }
    try {
      await onAsk(trimmed);
      setQuestion("");
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Ask failed. Try again.";
      setError(message);
    }
  };

  return (
    <Card className="flex flex-col gap-3">
      <div>
        <h3 className="text-sm font-semibold">Ask this deal room</h3>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Questions are answered strictly from the documents uploaded here.
          Citations point back to the source chunks.
        </p>
      </div>
      <form className="flex flex-col gap-2" onSubmit={submit}>
        <textarea
          className="min-h-24 w-full resize-y rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-400 dark:border-slate-700 dark:bg-slate-900"
          value={question}
          onChange={(event) => {
            setError(null);
            setQuestion(event.target.value);
          }}
          placeholder={
            hasDocuments
              ? "e.g. What are the main risks noted for the target?"
              : "Upload a document first, then ask a question."
          }
          maxLength={2000}
          disabled={isAsking}
        />
        <FieldError>{error}</FieldError>
        <div className="flex items-center justify-between gap-2">
          <span className="text-xs text-slate-400">
            {question.length}/2000
          </span>
          <Button type="submit" disabled={isAsking || question.trim().length === 0}>
            {isAsking ? "Asking..." : "Ask"}
          </Button>
        </div>
      </form>

      {latestAnswer ? (
        <AnswerCard
          answer={latestAnswer.answer}
          citations={latestAnswer.citations}
          model={latestAnswer.model}
          chunksUsed={latestAnswer.chunks_used}
        />
      ) : null}
    </Card>
  );
}
