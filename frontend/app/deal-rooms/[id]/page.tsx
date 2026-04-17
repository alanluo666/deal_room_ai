"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { use } from "react";

import { DocumentList } from "@/components/DocumentList";
import { DocumentUploader } from "@/components/DocumentUploader";
import { Button, Card } from "@/components/ui";
import { apiFetch } from "@/lib/api";
import { useLogout, useUser } from "@/lib/auth";
import type { DealRoom, DealRoomDocument } from "@/lib/types";

export default function DealRoomDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const dealRoomId = Number(id);

  const router = useRouter();
  const qc = useQueryClient();
  const { data: user } = useUser();
  const logout = useLogout();

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
    onSuccess: () =>
      qc.invalidateQueries({
        queryKey: ["deal-room", dealRoomId, "documents"],
      }),
  });

  const deleteMutation = useMutation<void, Error, number>({
    mutationFn: (documentId) =>
      apiFetch<void>(
        `/deal-rooms/${dealRoomId}/documents/${documentId}`,
        { method: "DELETE" },
      ),
    onSuccess: () =>
      qc.invalidateQueries({
        queryKey: ["deal-room", dealRoomId, "documents"],
      }),
  });

  const onLogout = async () => {
    await logout.mutateAsync();
    router.push("/login");
    router.refresh();
  };

  if (!Number.isFinite(dealRoomId)) {
    return (
      <main className="mx-auto max-w-4xl p-6">
        <Card>
          <p className="text-sm text-red-600">Invalid deal room id.</p>
        </Card>
      </main>
    );
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col gap-6 p-6">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <Link
            href="/deal-rooms"
            className="text-sm text-slate-500 hover:underline dark:text-slate-400"
          >
            &larr; All deal rooms
          </Link>
          <h1 className="mt-1 truncate text-2xl font-semibold">
            {roomQuery.data?.name ?? "Deal room"}
          </h1>
          {roomQuery.data?.target_company ? (
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Target: {roomQuery.data.target_company}
            </p>
          ) : null}
          {user ? (
            <p className="text-xs text-slate-400 dark:text-slate-500">
              Signed in as {user.email}
            </p>
          ) : null}
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={onLogout}>
            Sign out
          </Button>
        </div>
      </header>

      {roomQuery.isLoading ? (
        <p className="text-sm text-slate-500">Loading deal room...</p>
      ) : null}

      {roomQuery.isError ? (
        <Card>
          <p className="text-sm text-red-600">
            Could not load this deal room. It may have been deleted or you
            may not have access.
          </p>
        </Card>
      ) : null}

      {roomQuery.data ? (
        <>
          <DocumentUploader
            isUploading={uploadMutation.isPending}
            onUpload={async (file) => {
              await uploadMutation.mutateAsync(file);
            }}
          />

          {uploadMutation.isError ? (
            <p className="text-sm text-red-600">
              Upload failed: {uploadMutation.error.message}
            </p>
          ) : null}

          {documentsQuery.isLoading ? (
            <p className="text-sm text-slate-500">Loading documents...</p>
          ) : null}

          {documentsQuery.data ? (
            <DocumentList
              documents={documentsQuery.data}
              onDelete={(documentId) => deleteMutation.mutate(documentId)}
              pendingDeleteId={
                deleteMutation.isPending
                  ? (deleteMutation.variables ?? null)
                  : null
              }
            />
          ) : null}
        </>
      ) : null}
    </main>
  );
}
