"use client";

import { useState } from "react";

import { Button } from "./ui";

interface Props {
  onConfirm: () => Promise<void>;
  isDeleting: boolean;
  errorMessage?: string | null;
}

export function DeleteDealRoomButton({
  onConfirm,
  isDeleting,
  errorMessage,
}: Props) {
  const [confirming, setConfirming] = useState(false);

  if (!confirming) {
    return (
      <div className="flex flex-col items-end gap-1">
        <Button
          type="button"
          variant="ghost"
          className="text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950"
          onClick={() => setConfirming(true)}
          disabled={isDeleting}
        >
          Delete deal room
        </Button>
        {errorMessage ? (
          <p className="text-xs text-red-600">{errorMessage}</p>
        ) : null}
      </div>
    );
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <div className="flex items-center gap-2 rounded-md border border-red-200 bg-red-50 px-2 py-1 dark:border-red-900 dark:bg-red-950">
        <span className="text-xs text-red-700 dark:text-red-300">
          Delete this deal room and all its documents and questions?
        </span>
        <Button
          type="button"
          variant="danger"
          onClick={async () => {
            try {
              await onConfirm();
            } catch {
              // Parent surfaces the failure via errorMessage.
              setConfirming(false);
            }
          }}
          disabled={isDeleting}
        >
          {isDeleting ? "Deleting..." : "Confirm delete"}
        </Button>
        <Button
          type="button"
          variant="secondary"
          onClick={() => setConfirming(false)}
          disabled={isDeleting}
        >
          Cancel
        </Button>
      </div>
      {errorMessage ? (
        <p className="text-xs text-red-600">{errorMessage}</p>
      ) : null}
    </div>
  );
}
