"use client";

/**
 * ChatPanel — Person C step 3.
 *
 * Thin, self-contained conversation UI that sits next to AskPanel on the deal
 * room page. Design notes:
 *
 * - State is local. The component owns `turns`; the parent only provides an
 *   `onSend(messages)` prop and wires it to POST /deal-rooms/{id}/chat with
 *   React Query. Same prop-shape convention as AskPanel / AnalyzePanel.
 * - Each submit sends the full cumulative history. The backend currently
 *   only consumes the last user turn, but Person A's ADK agent will use the
 *   whole history later; keeping the wire format stable avoids a frontend
 *   edit when that swap happens.
 * - Local-dev safety: when the server's most recent reply carries
 *   `model === "local-dev-stub"` we show a muted banner explaining the
 *   placeholder state. The panel makes no other assumption about whether a
 *   real LLM answered — it renders `response.message.content` verbatim.
 * - Error handling is intentionally minimal: the inline error appears,
 *   the turn stays visible, the conversation is never wiped.
 */

import { useState } from "react";

import type { ChatMessage, ChatResponse, Citation } from "@/lib/types";

import { CitationList } from "./CitationList";
import { Button, Card, FieldError } from "./ui";

const LOCAL_DEV_STUB_MODEL = "local-dev-stub";
const MAX_CONTENT_LENGTH = 4000;

interface ChatTurn {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  model?: string;
  chunksUsed?: number;
}

interface Props {
  onSend: (messages: ChatMessage[]) => Promise<ChatResponse>;
  hasDocuments: boolean;
}

export function ChatPanel({ onSend, hasDocuments }: Props) {
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [draft, setDraft] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const lastAssistant = [...turns].reverse().find((t) => t.role === "assistant");
  const isStubMode = lastAssistant?.model === LOCAL_DEV_STUB_MODEL;

  const submit = async () => {
    setError(null);
    const trimmed = draft.trim();
    if (!trimmed) {
      setError("Type a message first.");
      return;
    }

    const userTurn: ChatTurn = { role: "user", content: trimmed };
    const nextTurns: ChatTurn[] = [...turns, userTurn];
    setTurns(nextTurns);
    setDraft("");
    setIsSending(true);

    try {
      const payload: ChatMessage[] = nextTurns.map(({ role, content }) => ({
        role,
        content,
      }));
      const response = await onSend(payload);
      const assistantTurn: ChatTurn = {
        role: "assistant",
        content: response.message.content,
        citations: response.citations,
        model: response.model,
        chunksUsed: response.chunks_used,
      };
      setTurns((prev) => [...prev, assistantTurn]);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Chat failed. Try again.";
      setError(message);
    } finally {
      setIsSending(false);
    }
  };

  const onSubmitForm = (event: React.FormEvent) => {
    event.preventDefault();
    if (!isSending) void submit();
  };

  const onTextareaKeyDown = (
    event: React.KeyboardEvent<HTMLTextAreaElement>,
  ) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (!isSending) void submit();
    }
  };

  return (
    <Card className="flex flex-col gap-3">
      <div>
        <h3 className="text-sm font-semibold">Chat with this deal room</h3>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Multi-turn conversation grounded in the uploaded documents. Citations
          appear below each assistant reply.
        </p>
      </div>

      {isStubMode ? (
        <div className="rounded-md border border-amber-300 bg-amber-50 p-2 text-xs text-amber-900 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-200">
          <strong>Local-dev stub mode.</strong> OpenAI is not configured on the
          server, so replies are placeholder text — not grounded answers from
          your documents. Set <code>OPENAI_API_KEY</code> and restart the API to
          get real answers.
        </div>
      ) : null}

      {turns.length > 0 ? (
        <ol className="flex flex-col gap-3">
          {turns.map((turn, idx) => (
            <li
              key={idx}
              className={
                turn.role === "user"
                  ? "max-w-[85%] self-end rounded-md bg-slate-900 px-3 py-2 text-sm text-white dark:bg-slate-200 dark:text-slate-900"
                  : "w-full self-start rounded-md border border-slate-200 bg-slate-50 p-3 text-sm dark:border-slate-800 dark:bg-slate-950"
              }
            >
              <p className="whitespace-pre-wrap">{turn.content}</p>
              {turn.role === "assistant" && turn.citations ? (
                <CitationList citations={turn.citations} />
              ) : null}
              {turn.role === "assistant" && turn.model ? (
                <p className="mt-2 text-xs text-slate-400">
                  model: {turn.model}
                  {typeof turn.chunksUsed === "number"
                    ? ` · ${turn.chunksUsed} chunk${
                        turn.chunksUsed === 1 ? "" : "s"
                      } used`
                    : ""}
                </p>
              ) : null}
            </li>
          ))}
          {isSending ? (
            <li className="self-start text-xs text-slate-500">
              Assistant is thinking…
            </li>
          ) : null}
        </ol>
      ) : null}

      <form className="flex flex-col gap-2" onSubmit={onSubmitForm}>
        <textarea
          className="min-h-24 w-full resize-y rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-400 dark:border-slate-700 dark:bg-slate-900"
          value={draft}
          onChange={(event) => {
            setError(null);
            setDraft(event.target.value);
          }}
          onKeyDown={onTextareaKeyDown}
          placeholder={
            hasDocuments
              ? "Ask about the deal. Enter to send, Shift+Enter for newline."
              : "Upload a document first, then start chatting."
          }
          maxLength={MAX_CONTENT_LENGTH}
          disabled={isSending}
        />
        <FieldError>{error}</FieldError>
        <div className="flex items-center justify-between gap-2">
          <span className="text-xs text-slate-400">
            {draft.length}/{MAX_CONTENT_LENGTH}
          </span>
          <Button
            type="submit"
            disabled={isSending || draft.trim().length === 0}
          >
            {isSending ? "Sending…" : "Send"}
          </Button>
        </div>
      </form>
    </Card>
  );
}
