"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Building2Icon, Loader2Icon } from "@/components/icons";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { FieldError } from "@/components/ui/field-error";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/lib/api";
import { useRegister } from "@/lib/auth";

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8, "At least 8 characters"),
});

type FormValues = z.infer<typeof schema>;

export default function RegisterPage() {
  const router = useRouter();
  const registerMutation = useRegister();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = async (values: FormValues) => {
    try {
      await registerMutation.mutateAsync(values);
      router.push("/deal-rooms");
      router.refresh();
    } catch (error) {
      const message =
        error instanceof ApiError ? error.message : "Registration failed";
      setError("root", { message });
    }
  };

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-background p-6">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,_hsl(var(--primary)/0.12),_transparent_55%)]"
      />
      <div className="relative w-full max-w-sm">
        <div className="mb-6 flex items-center justify-center gap-2">
          <span className="flex h-9 w-9 items-center justify-center rounded-md bg-primary text-primary-foreground shadow-soft">
            <Building2Icon className="h-5 w-5" aria-hidden="true" />
          </span>
          <span className="text-base font-semibold tracking-tight">
            Deal Room AI
          </span>
        </div>
        <Card className="flex flex-col gap-4 shadow-elevated">
          <div>
            <h1 className="text-xl font-semibold tracking-tight">
              Create your account
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Spin up your first deal room in seconds.
            </p>
          </div>
          <form
            className="flex flex-col gap-4"
            onSubmit={handleSubmit(onSubmit)}
            noValidate
          >
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                placeholder="you@company.com"
                aria-invalid={!!errors.email}
                {...register("email")}
              />
              <FieldError>{errors.email?.message}</FieldError>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                autoComplete="new-password"
                placeholder="At least 8 characters"
                aria-invalid={!!errors.password}
                {...register("password")}
              />
              <FieldError>{errors.password?.message}</FieldError>
            </div>
            {errors.root?.message ? (
              <div
                role="alert"
                className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
              >
                {errors.root.message}
              </div>
            ) : null}
            <Button type="submit" disabled={isSubmitting} size="lg">
              {isSubmitting ? (
                <>
                  <Loader2Icon
                    className="h-4 w-4 animate-spin"
                    aria-hidden="true"
                  />
                  Creating account…
                </>
              ) : (
                "Create account"
              )}
            </Button>
          </form>
          <p className="text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link
              className="font-medium text-primary underline-offset-4 hover:underline"
              href="/login"
            >
              Sign in
            </Link>
          </p>
        </Card>
      </div>
    </main>
  );
}
