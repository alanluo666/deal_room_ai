"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { DealRoomCard } from "@/components/DealRoomCard";
import { Building2Icon, PlusIcon, SearchIcon } from "@/components/icons";
import { EmptyState } from "@/components/shell/EmptyState";
import { DealRoomGridSkeleton } from "@/components/shell/Skeletons";
import { Button, FieldError, Input, Label } from "@/components/ui";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { toast } from "@/components/ui/toaster";
import { apiFetch } from "@/lib/api";
import { useUser } from "@/lib/auth";
import type { DealRoom, DealRoomCreateInput } from "@/lib/types";

const createSchema = z.object({
  name: z.string().min(1, "Required").max(255),
  target_company: z
    .string()
    .max(255)
    .optional()
    .transform((v) => (v && v.length > 0 ? v : undefined)),
});

type CreateValues = z.infer<typeof createSchema>;

type SortOrder = "newest" | "oldest" | "name-asc";

export default function DealRoomsPage() {
  const { data: user } = useUser();
  const qc = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [sortOrder, setSortOrder] = useState<SortOrder>("newest");

  const listQuery = useQuery<DealRoom[]>({
    queryKey: ["deal-rooms"],
    queryFn: () => apiFetch<DealRoom[]>("/deal-rooms"),
  });

  const createMutation = useMutation({
    mutationFn: (input: DealRoomCreateInput) =>
      apiFetch<DealRoom>("/deal-rooms", {
        method: "POST",
        body: JSON.stringify(input),
      }),
    onSuccess: (room) => {
      qc.invalidateQueries({ queryKey: ["deal-rooms"] });
      toast.success("Deal room created", { description: room.name });
    },
    onError: (error: Error) => {
      toast.error("Could not create deal room", {
        description: error.message,
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) =>
      apiFetch<void>(`/deal-rooms/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["deal-rooms"] });
      toast.success("Deal room deleted");
    },
    onError: (error: Error) => {
      toast.error("Could not delete deal room", {
        description: error.message,
      });
    },
  });

  const visibleRooms = useMemo(() => {
    const rooms = listQuery.data ?? [];
    const query = search.trim().toLowerCase();
    const filtered = query
      ? rooms.filter((room) => {
          const name = room.name.toLowerCase();
          const target = (room.target_company ?? "").toLowerCase();
          return name.includes(query) || target.includes(query);
        })
      : rooms;

    const sorted = [...filtered];
    if (sortOrder === "name-asc") {
      sorted.sort((a, b) => a.name.localeCompare(b.name));
    } else {
      sorted.sort((a, b) => {
        const diff =
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        return sortOrder === "newest" ? diff : -diff;
      });
    }
    return sorted;
  }, [listQuery.data, search, sortOrder]);

  const form = useForm<CreateValues>({ resolver: zodResolver(createSchema) });
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = form;

  useEffect(() => {
    if (!dialogOpen) reset();
  }, [dialogOpen, reset]);

  const onCreate = async (values: CreateValues) => {
    await createMutation.mutateAsync(values);
    setDialogOpen(false);
  };

  const total = listQuery.data?.length ?? 0;
  const shown = visibleRooms.length;
  const filtering = search.trim().length > 0 && shown !== total;

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
      <header className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Deal rooms</h1>
          <p className="text-sm text-muted-foreground">
            {user
              ? `Signed in as ${user.email}. Workspaces where you organize diligence materials and ask grounded questions.`
              : "Workspaces where you organize diligence materials and ask grounded questions."}
          </p>
        </div>
        <Button onClick={() => setDialogOpen(true)}>
          <PlusIcon />
          New deal room
        </Button>
      </header>

      {listQuery.data && listQuery.data.length > 0 ? (
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="relative flex-1">
            <SearchIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search deal rooms by name or target company"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              aria-label="Search deal rooms"
              className="pl-9"
            />
          </div>
          <label className="flex items-center gap-2 text-sm text-muted-foreground">
            <span className="shrink-0">Sort</span>
            <select
              value={sortOrder}
              onChange={(event) =>
                setSortOrder(event.target.value as SortOrder)
              }
              className="h-10 rounded-md border border-input bg-background px-3 text-sm shadow-soft focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              aria-label="Sort deal rooms"
            >
              <option value="newest">Newest first</option>
              <option value="oldest">Oldest first</option>
              <option value="name-asc">Name A–Z</option>
            </select>
          </label>
        </div>
      ) : null}

      {listQuery.data && listQuery.data.length > 0 ? (
        <p className="-mt-2 text-xs text-muted-foreground">
          {filtering
            ? `Showing ${shown} of ${total} ${total === 1 ? "deal room" : "deal rooms"}`
            : `${total} ${total === 1 ? "deal room" : "deal rooms"}`}
        </p>
      ) : null}

      {listQuery.isLoading ? <DealRoomGridSkeleton /> : null}

      {listQuery.isError ? (
        <EmptyState
          icon={Building2Icon}
          title="Could not load deal rooms"
          description="Something went wrong fetching your workspaces. Try refreshing."
          action={
            <Button variant="secondary" onClick={() => listQuery.refetch()}>
              Retry
            </Button>
          }
        />
      ) : null}

      {listQuery.data && listQuery.data.length === 0 ? (
        <EmptyState
          icon={Building2Icon}
          title="No deal rooms yet"
          description="Create your first deal room to upload diligence documents and ask grounded questions."
          action={
            <Button onClick={() => setDialogOpen(true)}>
              <PlusIcon />
              Create deal room
            </Button>
          }
        />
      ) : null}

      {listQuery.data && visibleRooms.length === 0 && total > 0 ? (
        <EmptyState
          icon={SearchIcon}
          title="No matches"
          description={`No deal rooms match "${search}".`}
          action={
            <Button variant="secondary" onClick={() => setSearch("")}>
              Clear search
            </Button>
          }
        />
      ) : null}

      {visibleRooms.length > 0 ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {visibleRooms.map((room) => (
            <DealRoomCard
              key={room.id}
              dealRoom={room}
              onDelete={(id) => deleteMutation.mutate(id)}
              deleting={
                deleteMutation.isPending &&
                deleteMutation.variables === room.id
              }
            />
          ))}
        </div>
      ) : null}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>New deal room</DialogTitle>
            <DialogDescription>
              A deal room scopes a set of documents, citations, and chat
              sessions to a single diligence effort.
            </DialogDescription>
          </DialogHeader>
          <form
            className="flex flex-col gap-3 pt-4"
            onSubmit={handleSubmit(onCreate)}
          >
            <div className="flex flex-col gap-1">
              <Label htmlFor="name">Name</Label>
              <Input id="name" data-autofocus {...register("name")} />
              <FieldError>{errors.name?.message}</FieldError>
            </div>
            <div className="flex flex-col gap-1">
              <Label htmlFor="target_company">Target company (optional)</Label>
              <Input id="target_company" {...register("target_company")} />
              <FieldError>{errors.target_company?.message}</FieldError>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="secondary"
                onClick={() => setDialogOpen(false)}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Creating…" : "Create deal room"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
