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
    <Card className="flex flex-col gap-4">
      <div>
        <div className="flex items-center gap-2">
          <MessageCircleIcon
            className="h-4 w-4 text-primary"
            aria-hidden="true"
          />
          <h3 className="text-sm font-semibold">Ask this deal room</h3>
        </div>
        <p className="mt-1 text-xs text-muted-foreground">
          Questions are answered strictly from the documents uploaded here.
          Citations point back to the source chunks.
        </p>
      </div>
      <form className="flex flex-col gap-2" onSubmit={submit}>
        <textarea
          className="min-h-[96px] w-full resize-y rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:ring-offset-background"
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
        />
        <FieldError>{error}</FieldError>
        <div className="flex items-center justify-between gap-2">
          <span className="text-xs text-muted-foreground">
            {question.length}/{MAX_QUESTION_LENGTH}
          </span>
          <Button
            type="submit"
            disabled={isAsking || question.trim().length === 0}
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
