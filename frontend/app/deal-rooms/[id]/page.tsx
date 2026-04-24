"use client";

import Link from "next/link";
import { use, useState } from "react";

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
  Building2Icon,
  FileTextIcon,
  MessageCircleIcon,
  MoreHorizontalIcon,
  SparklesIcon,
  TrashIcon,
} from "@/components/icons";
import {
  DealRoomHeaderSkeleton,
  DocumentListSkeleton,
} from "@/components/shell/Skeletons";
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
import { useDealRoom } from "@/lib/hooks/useDealRoom";
import { formatRelativeTime } from "@/lib/utils";

export default function DealRoomDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const dealRoomId = Number(id);

  const [tab, setTab] = useState("documents");
  const [deleteOpen, setDeleteOpen] = useState(false);

  const {
    isValidId,
    roomQuery,
    documentsQuery,
    documents,
    hasDocuments,
    uploadMutation,
    deleteDocumentMutation,
    questionsQuery,
    askMutation,
    latestAnswer,
    analyzeMutation,
    pendingAnalyzeTask,
    latestSummary,
    latestRisks,
    chatMutation,
    deleteRoomMutation,
  } = useDealRoom(dealRoomId);

  if (!isValidId) {
    return (
      <Card>
        <p className="text-sm text-destructive">Invalid deal room id.</p>
      </Card>
    );
  }

  const room = roomQuery.data;
  const docCount = documents.length;
  const pastQuestions = questionsQuery.data ?? [];

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
      <div>
        <Link
          href="/deal-rooms"
          className="inline-flex items-center gap-1.5 rounded-md text-sm text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
        >
          <ArrowLeftIcon className="h-3.5 w-3.5" aria-hidden="true" />
          All deal rooms
        </Link>
      </div>

      {roomQuery.isLoading ? <DealRoomHeaderSkeleton /> : null}

      {roomQuery.isError ? (
        <Card className="flex items-start gap-3 border-destructive/30 bg-destructive/5">
          <AlertTriangleIcon
            className="mt-0.5 h-5 w-5 text-destructive"
            aria-hidden="true"
          />
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
          <Card className="relative overflow-hidden p-0">
            <div
              aria-hidden="true"
              className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/60 to-transparent"
            />
            <div
              aria-hidden="true"
              className="pointer-events-none absolute -right-24 -top-24 h-64 w-64 rounded-full bg-primary/5 blur-3xl"
            />
            <div className="relative flex flex-col gap-5 p-6 sm:flex-row sm:items-start sm:justify-between sm:p-7">
              <div className="flex min-w-0 flex-1 items-start gap-4">
                <span
                  aria-hidden="true"
                  className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500/15 to-indigo-500/5 text-primary ring-1 ring-primary/20"
                >
                  <Building2Icon className="h-6 w-6" />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">
                    Deal room
                  </p>
                  <h1 className="mt-0.5 truncate text-2xl font-semibold tracking-tight text-foreground sm:text-[1.6rem]">
                    {room.name}
                  </h1>
                  <dl className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm">
                    {room.target_company ? (
                      <MetaItem
                        label="Target"
                        value={room.target_company}
                        accent
                      />
                    ) : null}
                    <MetaItem
                      label="Documents"
                      value={
                        documentsQuery.isLoading
                          ? "…"
                          : `${docCount} ${
                              docCount === 1 ? "document" : "documents"
                            }`
                      }
                    />
                    <MetaItem
                      label="Created"
                      value={formatRelativeTime(new Date(room.created_at))}
                      title={new Date(room.created_at).toLocaleString()}
                    />
                  </dl>
                </div>
              </div>
              <div className="flex items-center gap-2 self-start">
                <DropdownMenu>
                  <DropdownMenuTrigger
                    aria-label="Deal room actions"
                    className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-input bg-background text-muted-foreground shadow-soft transition-colors hover:bg-accent hover:text-foreground"
                  >
                    <MoreHorizontalIcon
                      className="h-4 w-4"
                      aria-hidden="true"
                    />
                  </DropdownMenuTrigger>
                  <DropdownMenuContent>
                    <DropdownMenuItem
                      destructive
                      onClick={() => setDeleteOpen(true)}
                    >
                      <TrashIcon className="h-4 w-4" aria-hidden="true" />
                      Delete deal room
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>
          </Card>

          <Tabs value={tab} onValueChange={setTab} variant="underline">
            <TabsList className="w-full overflow-x-auto">
              <TabsTrigger value="documents">
                <FileTextIcon className="h-4 w-4" aria-hidden="true" />
                Documents
                {docCount > 0 ? (
                  <span
                    aria-hidden="true"
                    className="ml-1 rounded-full bg-muted px-1.5 py-0.5 text-[10px] font-semibold tabular-nums text-muted-foreground"
                  >
                    {docCount}
                  </span>
                ) : null}
              </TabsTrigger>
              <TabsTrigger value="findings">
                <SparklesIcon className="h-4 w-4" aria-hidden="true" />
                Findings
              </TabsTrigger>
              <TabsTrigger value="ask">
                <MessageCircleIcon className="h-4 w-4" aria-hidden="true" />
                Ask
                {pastQuestions.length > 0 ? (
                  <span
                    aria-hidden="true"
                    className="ml-1 rounded-full bg-muted px-1.5 py-0.5 text-[10px] font-semibold tabular-nums text-muted-foreground"
                  >
                    {pastQuestions.length}
                  </span>
                ) : null}
              </TabsTrigger>
              <TabsTrigger value="chat">
                <BotIcon className="h-4 w-4" aria-hidden="true" />
                Chat
              </TabsTrigger>
            </TabsList>

            <TabsContent value="documents" className="flex flex-col gap-4">
              <SectionHeader
                icon={FileTextIcon}
                title="Data room"
                description="Upload and manage the documents indexed into this deal room."
              />
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
                  onDelete={(documentId) =>
                    deleteDocumentMutation.mutate(documentId)
                  }
                  pendingDeleteId={
                    deleteDocumentMutation.isPending
                      ? (deleteDocumentMutation.variables ?? null)
                      : null
                  }
                />
              )}
            </TabsContent>

            <TabsContent value="findings" className="flex flex-col gap-4">
              <SectionHeader
                icon={SparklesIcon}
                title="AI findings"
                description="Grounded summary and risks generated from the uploaded documents."
              />
              <FindingsPanel
                hasDocuments={hasDocuments}
                pendingTask={pendingAnalyzeTask}
                latestSummary={latestSummary}
                latestRisks={latestRisks}
                onAnalyze={async (task) => analyzeMutation.mutateAsync(task)}
              />
            </TabsContent>

            <TabsContent value="ask" className="flex flex-col gap-4">
              <SectionHeader
                icon={MessageCircleIcon}
                title="Research"
                description="Ask grounded questions and browse your past queries for this deal room."
              />
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
              <SectionHeader
                icon={BotIcon}
                title="Diligence analyst"
                description="Multi-turn conversation grounded in the uploaded documents."
              />
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

interface MetaItemProps {
  label: string;
  value: string;
  accent?: boolean;
  title?: string;
}

function MetaItem({ label, value, accent, title }: MetaItemProps) {
  return (
    <div className="flex min-w-0 items-center gap-2" title={title}>
      <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </dt>
      <dd
        className={
          accent
            ? "truncate font-medium text-foreground"
            : "truncate text-muted-foreground"
        }
      >
        {value}
      </dd>
    </div>
  );
}

interface SectionHeaderProps {
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  title: string;
  description: string;
}

function SectionHeader({ icon: Icon, title, description }: SectionHeaderProps) {
  return (
    <div className="flex items-start gap-3 pt-1">
      <span
        aria-hidden="true"
        className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary"
      >
        <Icon className="h-4 w-4" />
      </span>
      <div>
        <h2 className="text-base font-semibold tracking-tight">{title}</h2>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
    </div>
  );
}
