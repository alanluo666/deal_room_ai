"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState } from "react";
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

export default function DealRoomsPage() {
  const router = useRouter();
  const { data: user } = useUser();
  const logout = useLogout();
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);

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
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {listQuery.data.map((room) => (
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
    </main>
  );
}
