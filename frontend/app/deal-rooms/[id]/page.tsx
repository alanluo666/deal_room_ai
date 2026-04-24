"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { use, useState } from "react";

import { AnalyzePanel } from "@/components/AnalyzePanel";
import { AskPanel } from "@/components/AskPanel";
import { ChatPanel } from "@/components/ChatPanel";
import { DocumentList } from "@/components/DocumentList";
import { DocumentUploader } from "@/components/DocumentUploader";
import { FindingsPanel } from "@/components/FindingsPanel";
import { QuestionHistory } from "@/components/QuestionHistory";
import {
  AlertTriangleIcon,
  ArrowLeftIcon,
  BotIcon,
  FileTextIcon,
  MessageCircleIcon,
  MoreHorizontalIcon,
  SparklesIcon,
  TrashIcon,
} from "@/components/icons";
import {
  AnswerCardSkeleton,
  DealRoomHeaderSkeleton,
  DocumentListSkeleton,
} from "@/components/shell/Skeletons";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
import { formatRelativeTime } from "@/lib/utils";

export default function DealRoomDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const dealRoomId = Number(id);

  const router = useRouter();
  const qc = useQueryClient();

  const [tab, setTab] = useState("documents");
  const [deleteOpen, setDeleteOpen] = useState(false);

  const roomQuery = useQuery<DealRoom>({
    queryKey: ["deal-room", dealRoomId],
    queryFn: () => apiFetch<DealRoom>(`/deal-rooms/${dealRoomId}`),
    enabled: Number.isFinite(dealRoomId),
  });

  const documentsQuery = useQuery<DealRoomDocument[]>({
    queryKey: ["deal-room", dealRoomId, "documents"],
    queryFn: () =>
      apiFetch<DealRoomDocument[]>(`/deal-rooms/${dealRoomId}/documents`),
    enabled: Number.isFinite(dealRoomId) && !!roomQuery.data,
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

  const deleteMutation = useMutation<void, Error, number>({
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

  const questionsQuery = useQuery<QuestionRead[]>({
    queryKey: ["deal-room", dealRoomId, "questions"],
    queryFn: () =>
      apiFetch<QuestionRead[]>(`/deal-rooms/${dealRoomId}/questions`),
    enabled: Number.isFinite(dealRoomId) && !!roomQuery.data,
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

  const pendingAnalyzeTask: AnalyzeTask | null =
    analyzeMutation.isPending && analyzeMutation.variables
      ? analyzeMutation.variables
      : null;

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

  if (!Number.isFinite(dealRoomId)) {
    return (
      <Card>
        <p className="text-sm text-destructive">Invalid deal room id.</p>
      </Card>
    );
  }

  const room = roomQuery.data;
  const documents = documentsQuery.data ?? [];
  const hasDocuments = documents.length > 0;

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
      <div>
        <Link
          href="/deal-rooms"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeftIcon className="h-3.5 w-3.5" />
          All deal rooms
        </Link>
      </div>

      {roomQuery.isLoading ? <DealRoomHeaderSkeleton /> : null}

      {roomQuery.isError ? (
        <Card className="flex items-start gap-3 border-destructive/30 bg-destructive/5">
          <AlertTriangleIcon className="mt-0.5 h-5 w-5 text-destructive" />
          <div>
            <p className="text-sm font-medium text-destructive">
              Could not load this deal room
            </p>
            <p className="text-sm text-muted-foreground">
              It may have been deleted or you may not have access.
            </p>
          </div>
        </Card>
      ) : null}

      {room ? (
        <>
          <Card className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div className="min-w-0 flex-1">
              <h1 className="truncate text-2xl font-semibold tracking-tight">
                {room.name}
              </h1>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                {room.target_company ? (
                  <Badge variant="outline" className="font-normal normal-case">
                    Target · {room.target_company}
                  </Badge>
                ) : null}
                <Badge variant="secondary" className="font-normal normal-case">
                  {documents.length} {documents.length === 1 ? "document" : "documents"}
                </Badge>
                <Badge variant="secondary" className="font-normal normal-case">
                  Created {formatRelativeTime(new Date(room.created_at))}
                </Badge>
              </div>
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger
                aria-label="Deal room actions"
                className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-input text-muted-foreground hover:bg-accent hover:text-foreground"
              >
                <MoreHorizontalIcon className="h-4 w-4" />
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem
                  destructive
                  onClick={() => setDeleteOpen(true)}
                >
                  <TrashIcon className="h-4 w-4" />
                  Delete deal room
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </Card>

          <Tabs value={tab} onValueChange={setTab}>
            <TabsList>
              <TabsTrigger value="documents">
                <FileTextIcon className="h-4 w-4" />
                Documents
              </TabsTrigger>
              <TabsTrigger value="findings">
                <SparklesIcon className="h-4 w-4" />
                Findings
              </TabsTrigger>
              <TabsTrigger value="ask">
                <MessageCircleIcon className="h-4 w-4" />
                Ask
              </TabsTrigger>
              <TabsTrigger value="chat">
                <BotIcon className="h-4 w-4" />
                Chat
              </TabsTrigger>
            </TabsList>

            <TabsContent value="documents" className="flex flex-col gap-4">
              <DocumentUploader
                isUploading={uploadMutation.isPending}
                onUpload={async (file) => {
                  await uploadMutation.mutateAsync(file);
                }}
              />
              {documentsQuery.isLoading ? (
                <DocumentListSkeleton />
              ) : (
                <DocumentList
                  documents={documents}
                  onDelete={(documentId) => deleteMutation.mutate(documentId)}
                  pendingDeleteId={
                    deleteMutation.isPending
                      ? (deleteMutation.variables ?? null)
                      : null
                  }
                />
              )}
            </TabsContent>

            <TabsContent value="findings" className="flex flex-col gap-4">
              <AnalyzePanel
                hasDocuments={hasDocuments}
                pendingTask={pendingAnalyzeTask}
                errorMessage={null}
                onAnalyze={async (task) => analyzeMutation.mutateAsync(task)}
              />
              {analyzeMutation.isPending && !latestSummary && !latestRisks ? (
                <AnswerCardSkeleton />
              ) : (
                <FindingsPanel
                  latestSummary={latestSummary}
                  latestRisks={latestRisks}
                />
              )}
            </TabsContent>

            <TabsContent value="ask" className="flex flex-col gap-4">
              <AskPanel
                isAsking={askMutation.isPending}
                latestAnswer={latestAnswer}
                hasDocuments={hasDocuments}
                onAsk={async (question) => askMutation.mutateAsync(question)}
              />
              {questionsQuery.data ? (
                <QuestionHistory questions={questionsQuery.data} />
              ) : null}
            </TabsContent>

            <TabsContent value="chat" className="flex flex-col gap-4">
              <ChatPanel
                hasDocuments={hasDocuments}
                onSend={async (messages) => chatMutation.mutateAsync(messages)}
              />
            </TabsContent>
          </Tabs>
        </>
      ) : null}

      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete this deal room?</DialogTitle>
            <DialogDescription>
              This permanently removes the deal room along with all uploaded
              documents and question history. This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              type="button"
              variant="secondary"
              onClick={() => setDeleteOpen(false)}
              disabled={deleteRoomMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="danger"
              onClick={async () => {
                try {
                  await deleteRoomMutation.mutateAsync();
                } catch {
                  /* toast handled in onError */
                }
              }}
              disabled={deleteRoomMutation.isPending}
            >
              {deleteRoomMutation.isPending ? "Deleting…" : "Delete deal room"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
