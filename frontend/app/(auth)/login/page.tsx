"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { DealRoomLogo } from "@/components/branding/DealRoomLogo";
import { Loader2Icon } from "@/components/icons";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { FieldError } from "@/components/ui/field-error";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/lib/api";
import { useLogin } from "@/lib/auth";

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(1, "Required"),
});

type FormValues = z.infer<typeof schema>;

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}

function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const next = params.get("next") ?? "/deal-rooms";
  const login = useLogin();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = async (values: FormValues) => {
    try {
      await login.mutateAsync(values);
      router.push(next);
      router.refresh();
    } catch (error) {
      const message =
        error instanceof ApiError ? error.message : "Login failed";
      setError("root", { message });
    }
  };

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-background p-6">
      <AuthBackdrop />
      <div className="relative w-full max-w-sm">
        <BrandLockup />
        <Card className="flex flex-col gap-5 border-border/80 p-6 shadow-elevated sm:p-7">
          <div className="space-y-1">
            <h1 className="text-xl font-semibold tracking-tight">
              Welcome back
            </h1>
            <p className="text-sm text-muted-foreground">
              Sign in to continue to your deal rooms.
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
                autoComplete="current-password"
                placeholder="••••••••"
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
                  Signing in…
                </>
              ) : (
                "Sign in"
              )}
            </Button>
          </form>
          <p className="text-center text-sm text-muted-foreground">
            Need an account?{" "}
            <Link
              className="font-medium text-primary underline-offset-4 hover:underline"
              href="/register"
            >
              Create one
            </Link>
          </p>
        </Card>
        <p className="mt-6 text-center text-xs text-muted-foreground">
          By signing in you agree to keep your diligence materials secure.
        </p>
      </div>
    </main>
  );
}

function BrandLockup() {
  return (
    <div className="mb-6 flex flex-col items-center gap-3 text-center">
      <DealRoomLogo
        variant="icon"
        className="h-12 w-12 drop-shadow-[0_6px_16px_rgba(79,70,229,0.35)]"
      />
      <div>
        <p className="text-base font-semibold tracking-tight">Deal Room AI</p>
        <p className="mt-0.5 text-xs text-muted-foreground">
          AI-powered due diligence workspace
        </p>
      </div>
    </div>
  );
}

function AuthBackdrop() {
  return (
    <>
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,_hsl(var(--primary)/0.12),_transparent_55%)]"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-0 top-0 h-[460px] bg-[linear-gradient(to_bottom,hsl(var(--primary)/0.04),transparent)]"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 [background-image:linear-gradient(to_right,hsl(var(--border))_1px,transparent_1px),linear-gradient(to_bottom,hsl(var(--border))_1px,transparent_1px)] [background-size:56px_56px] opacity-[0.35] [mask-image:radial-gradient(ellipse_at_center,black,transparent_70%)]"
      />
    </>
  );
}
