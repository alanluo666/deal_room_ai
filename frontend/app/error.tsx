"use client";

import { useEffect } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { AlertTriangleIcon } from "@/components/icons";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // eslint-disable-next-line no-console
    console.error("[app] unhandled render error", error);
  }, [error]);

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <Card className="flex w-full max-w-md flex-col items-center gap-4 text-center">
        <span className="flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10 text-destructive">
          <AlertTriangleIcon className="h-6 w-6" />
        </span>
        <div>
          <h1 className="text-lg font-semibold">Something went wrong</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            An unexpected error occurred while rendering this page. You can try
            again or head back to your deal rooms.
          </p>
          {error.digest ? (
            <p className="mt-2 text-xs text-muted-foreground">
              Error id: <code className="font-mono">{error.digest}</code>
            </p>
          ) : null}
        </div>
        <div className="flex w-full flex-col gap-2 sm:flex-row sm:justify-center">
          <Button onClick={reset}>Try again</Button>
          <Button
            variant="secondary"
            onClick={() => {
              window.location.href = "/deal-rooms";
            }}
          >
            Go to deal rooms
          </Button>
        </div>
      </Card>
    </main>
  );
}
