"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { DealRoomCard } from "@/components/DealRoomCard";
import { Button, Card, FieldError, Input, Label } from "@/components/ui";
import { apiFetch } from "@/lib/api";
import { useLogout, useUser } from "@/lib/auth";
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

// Toolbar state lives purely on the client. No backend /deal-rooms query
// params change; the full list is fetched once and filtered/sorted in memory.
type SortOrder = "newest" | "oldest" | "name-asc";

export default function DealRoomsPage() {
  const router = useRouter();
  const { data: user } = useUser();
  const logout = useLogout();
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);
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
    onSuccess: () => qc.invalidateQueries({ queryKey: ["deal-rooms"] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) =>
      apiFetch<void>(`/deal-rooms/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["deal-rooms"] }),
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

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CreateValues>({ resolver: zodResolver(createSchema) });

  const onCreate = async (values: CreateValues) => {
    await createMutation.mutateAsync(values);
    reset();
    setShowForm(false);
  };

  const onLogout = async () => {
    await logout.mutateAsync();
    router.push("/login");
    router.refresh();
  };

  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col gap-6 p-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Deal Rooms</h1>
          {user ? (
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Signed in as {user.email}
            </p>
          ) : null}
        </div>
        <div className="flex gap-2">
          <Button onClick={() => setShowForm((v) => !v)}>
            {showForm ? "Cancel" : "New deal room"}
          </Button>
          <Button variant="secondary" onClick={onLogout}>
            Sign out
          </Button>
        </div>
      </header>

      {showForm ? (
        <Card>
          <form
            className="flex flex-col gap-3"
            onSubmit={handleSubmit(onCreate)}
          >
            <div className="flex flex-col gap-1">
              <Label htmlFor="name">Name</Label>
              <Input id="name" {...register("name")} />
              <FieldError>{errors.name?.message}</FieldError>
            </div>
            <div className="flex flex-col gap-1">
              <Label htmlFor="target_company">Target company (optional)</Label>
              <Input id="target_company" {...register("target_company")} />
              <FieldError>{errors.target_company?.message}</FieldError>
            </div>
            <div className="flex justify-end">
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Creating..." : "Create deal room"}
              </Button>
            </div>
          </form>
        </Card>
      ) : null}

      {listQuery.isLoading ? (
        <p className="text-sm text-slate-500">Loading deal rooms...</p>
      ) : null}

      {listQuery.isError ? (
        <p className="text-sm text-red-600">
          Could not load deal rooms. Try refreshing.
        </p>
      ) : null}

      {listQuery.data && listQuery.data.length === 0 ? (
        <Card>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            You do not have any deal rooms yet. Click &ldquo;New deal
            room&rdquo; to create your first one.
          </p>
        </Card>
      ) : null}

      {listQuery.data && listQuery.data.length > 0 ? (
        <>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-3">
            <Input
              type="search"
              placeholder="Search deal rooms"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              aria-label="Search deal rooms"
              className="sm:flex-1"
            />
            <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
              <span className="shrink-0">Sort</span>
              <select
                value={sortOrder}
                onChange={(event) =>
                  setSortOrder(event.target.value as SortOrder)
                }
                className="rounded-md border border-slate-300 bg-white px-2 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-slate-400 dark:border-slate-700 dark:bg-slate-900"
                aria-label="Sort deal rooms"
              >
                <option value="newest">Newest first</option>
                <option value="oldest">Oldest first</option>
                <option value="name-asc">Name A–Z</option>
              </select>
            </label>
          </div>

          <p className="text-xs text-slate-500 dark:text-slate-400">
            {(() => {
              const total = listQuery.data.length;
              const shown = visibleRooms.length;
              const filtering = search.trim().length > 0 && shown !== total;
              const noun = total === 1 ? "deal room" : "deal rooms";
              return filtering
                ? `Showing ${shown} of ${total} ${noun}`
                : `${total} ${noun}`;
            })()}
          </p>

          {visibleRooms.length === 0 ? (
            <p className="text-sm text-slate-500 dark:text-slate-400">
              No deal rooms match your search.
            </p>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
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
          )}
        </>
      ) : null}
    </main>
  );
}
