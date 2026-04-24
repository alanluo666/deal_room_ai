"use client";

/**
 * ChatPanel — multi-turn grounded chat for a deal room.
 *
 * - State is local. The component owns `turns`; the parent only provides an
 *   `onSend(messages)` prop and wires it to POST /deal-rooms/{id}/chat.
 * - Each submit sends the full cumulative history so that future ADK-driven
 *   server behavior can consume history without a frontend change.
 * - Local-dev safety: when the most recent assistant reply reports
 *   `model === "local-dev-stub"` we surface a muted banner.
 * - Accessibility: the message list is marked `aria-live="polite"` so screen
 *   readers announce new assistant turns. We avoid server rendering any
 *   dynamic timestamp or locale-formatted text to sidestep hydration
 *   mismatches (see toaster.tsx for the same reasoning).
 */

import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from "react";

import {
  BotIcon,
  Loader2Icon,
  SendIcon,
  SparklesIcon,
  TrashIcon,
  UserIcon,
} from "@/components/icons";
import { EmptyState } from "@/components/shell/EmptyState";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { FieldError } from "@/components/ui/field-error";
import type { ChatMessage, ChatResponse, Citation } from "@/lib/types";
import { cn } from "@/lib/utils";

import { CitationChips } from "./CitationList";

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

  const scrollRef = useRef<HTMLDivElement | null>(null);

  const lastAssistant = useMemo(
    () => [...turns].reverse().find((t) => t.role === "assistant"),
    [turns],
  );
  const isStubMode = lastAssistant?.model === LOCAL_DEV_STUB_MODEL;

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [turns, isSending]);

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

  const onSubmitForm = (event: FormEvent) => {
    event.preventDefault();
    if (!isSending) void submit();
  };

  const onTextareaKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (!isSending) void submit();
    }
  };

  const clearConversation = () => {
    if (isSending) return;
    setTurns([]);
    setError(null);
  };

  const isEmpty = turns.length === 0;

  return (
    <Card className="flex flex-col gap-0 overflow-hidden p-0">
      <div className="flex items-start justify-between gap-3 border-b border-border bg-[linear-gradient(180deg,hsl(var(--primary)/0.05),transparent)] px-5 pb-4 pt-5">
        <div className="flex items-start gap-3">
          <span
            aria-hidden="true"
            className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary ring-1 ring-primary/15"
          >
            <BotIcon className="h-4 w-4" />
          </span>
          <div>
            <p className="text-[11px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
              Diligence analyst
            </p>
            <h3 className="text-sm font-semibold tracking-tight">
              Chat with this deal room
            </h3>
            <p className="mt-0.5 text-xs text-muted-foreground">
              Multi-turn conversation grounded in the uploaded documents.
              Citations are attached as source chips under each reply.
            </p>
          </div>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={clearConversation}
          disabled={isEmpty || isSending}
          aria-label="Clear conversation"
        >
          <TrashIcon className="h-3.5 w-3.5" aria-hidden="true" />
          Clear
        </Button>
      </div>

      {isStubMode ? (
        <div className="mx-5 mt-3 rounded-md border border-warning/50 bg-warning/10 px-3 py-2 text-xs text-warning-foreground">
          <strong className="font-medium">Local-dev stub mode.</strong>{" "}
          OpenAI is not configured on the server, so replies are placeholder
          text. Set <code>OPENAI_API_KEY</code> and restart the API to get
          real answers.
        </div>
      ) : null}

      <div
        ref={scrollRef}
        role="log"
        aria-live="polite"
        aria-relevant="additions"
        className="h-[460px] overflow-y-auto bg-muted/10 px-5 pb-2"
      >
        {isEmpty ? (
          <div className="flex h-full items-center justify-center py-6">
            <EmptyState
              icon={BotIcon}
              title={
                hasDocuments
                  ? "Start a conversation"
                  : "No documents yet"
              }
              description={
                hasDocuments
                  ? "Ask a question below to kick off a multi-turn chat."
                  : "Upload a document first, then start chatting."
              }
              className="border-0 bg-transparent"
            />
          </div>
        ) : (
          <ol className="flex flex-col gap-3 py-4">
            {turns.map((turn, idx) => (
              <li
                key={idx}
                className={cn(
                  "flex gap-3",
                  turn.role === "user" ? "justify-end" : "justify-start",
                )}
              >
                {turn.role === "assistant" ? (
                  <span
                    aria-hidden="true"
                    className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary"
                  >
                    <SparklesIcon className="h-4 w-4" />
                  </span>
                ) : null}
                <div
                  className={cn(
                    "max-w-[85%] rounded-2xl px-3.5 py-2.5 text-sm shadow-soft",
                    turn.role === "user"
                      ? "rounded-tr-sm bg-primary text-primary-foreground"
                      : "rounded-tl-sm border border-border bg-background text-foreground",
                  )}
                >
                  <p className="whitespace-pre-wrap leading-relaxed">
                    {turn.content}
                  </p>
                  {turn.role === "assistant" &&
                  turn.citations &&
                  turn.citations.length > 0 ? (
                    <div className="mt-2 space-y-1.5">
                      <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
                        Sources
                      </p>
                      <CitationChips citations={turn.citations} />
                    </div>
                  ) : null}
                  {turn.role === "assistant" && turn.model ? (
                    <div className="mt-2 flex flex-wrap items-center gap-1.5 border-t border-border/70 pt-2">
                      <Badge
                        variant="outline"
                        className="font-normal normal-case"
                      >
                        model · {turn.model}
                      </Badge>
                      {typeof turn.chunksUsed === "number" ? (
                        <Badge
                          variant="outline"
                          className="font-normal normal-case"
                        >
                          {turn.chunksUsed} chunk
                          {turn.chunksUsed === 1 ? "" : "s"} used
                        </Badge>
                      ) : null}
                    </div>
                  ) : null}
                </div>
                {turn.role === "user" ? (
                  <span
                    aria-hidden="true"
                    className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground"
                  >
                    <UserIcon className="h-4 w-4" />
                  </span>
                ) : null}
              </li>
            ))}
            {isSending ? (
              <li className="flex items-center gap-2 text-xs text-muted-foreground">
                <Loader2Icon className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
                Assistant is thinking…
              </li>
            ) : null}
          </ol>
        )}
      </div>

      <form
        className="sticky bottom-0 flex flex-col gap-2 border-t border-border bg-background/95 px-5 py-3 backdrop-blur supports-[backdrop-filter]:bg-background/80"
        onSubmit={onSubmitForm}
      >
        <textarea
          className="min-h-[72px] w-full resize-y rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:ring-offset-background"
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
          aria-label="Chat message"
        />
        <FieldError>{error}</FieldError>
        <div className="flex items-center justify-between gap-2">
          <span className="text-xs text-muted-foreground">
            {draft.length}/{MAX_CONTENT_LENGTH}
          </span>
          <Button
            type="submit"
            disabled={isSending || draft.trim().length === 0}
            aria-label="Send message"
          >
            {isSending ? (
              <>
                <Loader2Icon className="h-4 w-4 animate-spin" aria-hidden="true" />
                Sending…
              </>
            ) : (
              <>
                <SendIcon className="h-4 w-4" aria-hidden="true" />
                Send
              </>
            )}
          </Button>
        </div>
      </form>
    </Card>
  );
}
