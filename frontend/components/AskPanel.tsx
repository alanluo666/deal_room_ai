"use client";

import { useState } from "react";

import {
  Loader2Icon,
  MessageCircleIcon,
  SendIcon,
} from "@/components/icons";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { FieldError } from "@/components/ui/field-error";
import type { AskResponse } from "@/lib/types";

import { AnswerCard } from "./AnswerCard";

interface Props {
  onAsk: (question: string) => Promise<AskResponse>;
  isAsking: boolean;
  latestAnswer: AskResponse | null;
  hasDocuments: boolean;
}

const MAX_QUESTION_LENGTH = 2000;

export function AskPanel({
  onAsk,
  isAsking,
  latestAnswer,
  hasDocuments,
}: Props) {
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

  const disabled = !hasDocuments || isAsking;

  return (
    <div className="flex flex-col gap-4">
      <Card className="flex flex-col gap-4 overflow-hidden p-0">
        <div className="flex items-start gap-3 border-b border-border bg-[linear-gradient(180deg,hsl(var(--primary)/0.05),transparent)] px-5 pb-4 pt-5">
          <span
            aria-hidden="true"
            className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary ring-1 ring-primary/15"
          >
            <MessageCircleIcon className="h-4 w-4" />
          </span>
          <div>
            <p className="text-[11px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
              Research
            </p>
            <h3 className="text-sm font-semibold tracking-tight">
              Ask this deal room
            </h3>
            <p className="mt-0.5 text-xs text-muted-foreground">
              Answers are grounded strictly in this deal room&apos;s
              documents. Each response includes citations back to the source
              chunks.
            </p>
          </div>
        </div>
        <form className="flex flex-col gap-3 px-5 pb-5" onSubmit={submit}>
          <textarea
            className="min-h-[104px] w-full resize-y rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:ring-offset-background disabled:cursor-not-allowed disabled:opacity-70"
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
            maxLength={MAX_QUESTION_LENGTH}
            disabled={isAsking}
            aria-label="Question"
            aria-invalid={error ? true : undefined}
          />
          <FieldError>{error}</FieldError>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="text-xs tabular-nums text-muted-foreground">
              {question.length}/{MAX_QUESTION_LENGTH}
            </span>
            <Button
              type="submit"
              disabled={disabled || question.trim().length === 0}
              aria-label="Ask question"
            >
              {isAsking ? (
                <>
                  <Loader2Icon
                    className="h-4 w-4 animate-spin"
                    aria-hidden="true"
                  />
                  Asking…
                </>
              ) : (
                <>
                  <SendIcon className="h-4 w-4" aria-hidden="true" />
                  Ask
                </>
              )}
            </Button>
          </div>
        </form>
      </Card>

      {latestAnswer ? (
        <AnswerCard
          title="Latest answer"
          answer={latestAnswer.answer}
          citations={latestAnswer.citations}
          model={latestAnswer.model}
          chunksUsed={latestAnswer.chunks_used}
        />
      ) : null}
    </div>
  );
}
