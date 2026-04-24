"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";

import { toast } from "@/components/ui/toaster";
import { apiFetch } from "@/lib/api";
import type {
  AnalyzeResponse,
  AnalyzeTask,
  AskResponse,
  ChatMessage,
  ChatResponse,
  DealRoom,
  DealRoomDocument,
  QuestionRead,
} from "@/lib/types";

/**
 * Document-list poll interval. Only fires while at least one visible document
 * is still being processed. Chosen conservatively: 4s keeps the UI feeling
 * live without hammering the API, and the query is skipped entirely while the
 * list is already in a terminal state (ready or failed) for every row.
 */
const DOCUMENT_POLL_MS = 4000;

function isNonTerminal(doc: DealRoomDocument): boolean {
  return doc.status === "pending" || doc.status === "processing";
}

export interface UseDealRoomResult {
  dealRoomId: number;
  isValidId: boolean;

  roomQuery: UseQueryResult<DealRoom, Error>;
  documentsQuery: UseQueryResult<DealRoomDocument[], Error>;
  questionsQuery: UseQueryResult<QuestionRead[], Error>;

  documents: DealRoomDocument[];
  hasDocuments: boolean;

  uploadMutation: UseMutationResult<DealRoomDocument, Error, File>;
  deleteDocumentMutation: UseMutationResult<void, Error, number>;

  askMutation: UseMutationResult<AskResponse, Error, string>;
  latestAnswer: AskResponse | null;

  analyzeMutation: UseMutationResult<AnalyzeResponse, Error, AnalyzeTask>;
  pendingAnalyzeTask: AnalyzeTask | null;
  latestSummary: AnalyzeResponse | null;
  latestRisks: AnalyzeResponse | null;
  clearFindings: () => void;

  chatMutation: UseMutationResult<ChatResponse, Error, ChatMessage[]>;

  deleteRoomMutation: UseMutationResult<void, Error, void>;
}

/**
 * Centralizes every data hook that the deal-room detail page needs:
 *
 *   - room / documents / questions queries
 *   - upload, delete-document, ask, analyze, chat, delete-room mutations
 *   - the three ephemeral pieces of display-only state (latest answer,
 *     latest summary, latest risks)
 *
 * No new endpoints, no new cache keys, no new side effects vs. the previous
 * inline implementation in `app/deal-rooms/[id]/page.tsx` — this is purely a
 * composition-level extraction. The one intentional enhancement is opt-in
 * polling of the documents query while any row is still being processed
 * (Step 10 of the UI plan), gated so that healthy rooms do not poll.
 */
export function useDealRoom(dealRoomId: number): UseDealRoomResult {
  const router = useRouter();
  const qc = useQueryClient();
  const isValidId = Number.isFinite(dealRoomId);

  const roomQuery = useQuery<DealRoom, Error>({
    queryKey: ["deal-room", dealRoomId],
    queryFn: () => apiFetch<DealRoom>(`/deal-rooms/${dealRoomId}`),
    enabled: isValidId,
  });

  const documentsQuery = useQuery<DealRoomDocument[], Error>({
    queryKey: ["deal-room", dealRoomId, "documents"],
    queryFn: () =>
      apiFetch<DealRoomDocument[]>(`/deal-rooms/${dealRoomId}/documents`),
    enabled: isValidId && !!roomQuery.data,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (!data || data.length === 0) return false;
      return data.some(isNonTerminal) ? DOCUMENT_POLL_MS : false;
    },
  });

  const questionsQuery = useQuery<QuestionRead[], Error>({
    queryKey: ["deal-room", dealRoomId, "questions"],
    queryFn: () =>
      apiFetch<QuestionRead[]>(`/deal-rooms/${dealRoomId}/questions`),
    enabled: isValidId && !!roomQuery.data,
  });

  const uploadMutation = useMutation<DealRoomDocument, Error, File>({
    mutationFn: async (file) => {
      const body = new FormData();
      body.append("file", file);
      return apiFetch<DealRoomDocument>(
        `/deal-rooms/${dealRoomId}/documents`,
        { method: "POST", body },
      );
    },
    onSuccess: (doc) => {
      qc.invalidateQueries({
        queryKey: ["deal-room", dealRoomId, "documents"],
      });
      toast.success("Document uploaded", { description: doc.filename });
    },
    onError: (error) => {
      toast.error("Upload failed", { description: error.message });
    },
  });

  const deleteDocumentMutation = useMutation<void, Error, number>({
    mutationFn: (documentId) =>
      apiFetch<void>(
        `/deal-rooms/${dealRoomId}/documents/${documentId}`,
        { method: "DELETE" },
      ),
    onSuccess: () => {
      qc.invalidateQueries({
        queryKey: ["deal-room", dealRoomId, "documents"],
      });
    },
    onError: (error) => {
      toast.error("Could not remove document", { description: error.message });
    },
  });

  const [latestAnswer, setLatestAnswer] = useState<AskResponse | null>(null);
  const [latestSummary, setLatestSummary] = useState<AnalyzeResponse | null>(
    null,
  );
  const [latestRisks, setLatestRisks] = useState<AnalyzeResponse | null>(null);

  const askMutation = useMutation<AskResponse, Error, string>({
    mutationFn: (question) =>
      apiFetch<AskResponse>(`/deal-rooms/${dealRoomId}/ask`, {
        method: "POST",
        body: JSON.stringify({ question }),
      }),
    onSuccess: (data) => {
      setLatestAnswer(data);
      qc.invalidateQueries({
        queryKey: ["deal-room", dealRoomId, "questions"],
      });
    },
    onError: (error) => {
      toast.error("Ask failed", { description: error.message });
    },
  });

  const analyzeMutation = useMutation<AnalyzeResponse, Error, AnalyzeTask>({
    mutationFn: (task) =>
      apiFetch<AnalyzeResponse>(`/deal-rooms/${dealRoomId}/analyze`, {
        method: "POST",
        body: JSON.stringify({ task }),
      }),
    onSuccess: (data, task) => {
      if (task === "summary") setLatestSummary(data);
      else if (task === "risks") setLatestRisks(data);
    },
    onError: (error, task) => {
      toast.error(
        task === "summary" ? "Summary failed" : "Risk analysis failed",
        { description: error.message },
      );
    },
  });

  const chatMutation = useMutation<ChatResponse, Error, ChatMessage[]>({
    mutationFn: (messages) =>
      apiFetch<ChatResponse>(`/deal-rooms/${dealRoomId}/chat`, {
        method: "POST",
        body: JSON.stringify({ messages }),
      }),
  });

  const deleteRoomMutation = useMutation<void, Error, void>({
    mutationFn: () =>
      apiFetch<void>(`/deal-rooms/${dealRoomId}`, { method: "DELETE" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["deal-rooms"] });
      toast.success("Deal room deleted");
      router.push("/deal-rooms");
      router.refresh();
    },
    onError: (error) => {
      toast.error("Could not delete deal room", { description: error.message });
    },
  });

  const pendingAnalyzeTask: AnalyzeTask | null =
    analyzeMutation.isPending && analyzeMutation.variables
      ? analyzeMutation.variables
      : null;

  const documents = documentsQuery.data ?? [];

  const clearFindings = useCallback(() => {
    setLatestSummary(null);
    setLatestRisks(null);
  }, []);

  return {
    dealRoomId,
    isValidId,
    roomQuery,
    documentsQuery,
    questionsQuery,
    documents,
    hasDocuments: documents.length > 0,
    uploadMutation,
    deleteDocumentMutation,
    askMutation,
    latestAnswer,
    analyzeMutation,
    pendingAnalyzeTask,
    latestSummary,
    latestRisks,
    clearFindings,
    chatMutation,
    deleteRoomMutation,
  };
}
