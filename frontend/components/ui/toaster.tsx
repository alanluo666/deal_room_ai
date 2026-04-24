"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { cn } from "@/lib/utils";

import { Button } from "./button";
import {
  AlertCircleIcon,
  AlertTriangleIcon,
  CheckCircle2Icon,
  InfoIcon,
  XIcon,
} from "../icons";

/**
 * Minimal toast system with a `sonner`-inspired API:
 *
 *   toast("Uploaded")
 *   toast.success("Saved", { description: "..." })
 *   toast.error("Upload failed", { description: err.message })
 *
 * Implementation detail: a module-level bus lets non-React call sites (e.g.
 * mutation onError handlers) dispatch toasts without passing context around.
 * The <Toaster /> component subscribes to the bus and renders the stack.
 */

export type ToastVariant = "default" | "success" | "error" | "warning";

export interface ToastOptions {
  id?: string;
  description?: string;
  duration?: number;
}

interface ToastRecord {
  id: string;
  title: string;
  description?: string;
  variant: ToastVariant;
  duration: number;
}

type Listener = (toasts: ToastRecord[]) => void;

const DEFAULT_DURATION = 5000;

class ToastBus {
  private toasts: ToastRecord[] = [];
  private listeners = new Set<Listener>();

  subscribe(listener: Listener) {
    this.listeners.add(listener);
    listener(this.toasts);
    return () => {
      this.listeners.delete(listener);
    };
  }

  private emit() {
    for (const listener of this.listeners) listener(this.toasts);
  }

  push(variant: ToastVariant, title: string, options: ToastOptions = {}) {
    const id =
      options.id ??
      (typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : `toast-${Date.now()}-${Math.random().toString(36).slice(2)}`);
    const record: ToastRecord = {
      id,
      title,
      description: options.description,
      variant,
      duration: options.duration ?? DEFAULT_DURATION,
    };
    this.toasts = [...this.toasts, record];
    this.emit();
    return id;
  }

  dismiss(id: string) {
    this.toasts = this.toasts.filter((t) => t.id !== id);
    this.emit();
  }

  snapshot() {
    return this.toasts;
  }
}

const bus = new ToastBus();

type ToastFn = (title: string, options?: ToastOptions) => string;

interface ToastApi extends ToastFn {
  success: ToastFn;
  error: ToastFn;
  warning: ToastFn;
  info: ToastFn;
  dismiss: (id: string) => void;
}

const toastFn: ToastFn = (title, options) => bus.push("default", title, options);
const api = toastFn as ToastApi;
api.success = (title, options) => bus.push("success", title, options);
api.error = (title, options) => bus.push("error", title, options);
api.warning = (title, options) => bus.push("warning", title, options);
api.info = (title, options) => bus.push("default", title, options);
api.dismiss = (id) => bus.dismiss(id);

export const toast = api;

// React-side hook if callers want to render inline (currently unused but
// kept for parity with sonner/shadcn patterns).
const ToastCtx = createContext<ToastApi>(toast);
export function useToast() {
  return useContext(ToastCtx);
}

const VARIANT_ICON: Record<ToastVariant, ReactNode> = {
  default: <InfoIcon />,
  success: <CheckCircle2Icon />,
  error: <AlertCircleIcon />,
  warning: <AlertTriangleIcon />,
};

const VARIANT_CLASS: Record<ToastVariant, string> = {
  default: "border-border bg-popover text-popover-foreground",
  success: "border-success/30 bg-success/10 text-foreground",
  error: "border-destructive/30 bg-destructive/10 text-foreground",
  warning: "border-warning/40 bg-warning/15 text-foreground",
};

const VARIANT_ICON_CLASS: Record<ToastVariant, string> = {
  default: "text-muted-foreground",
  success: "text-success",
  error: "text-destructive",
  warning: "text-warning",
};

export function Toaster() {
  const [toasts, setToasts] = useState<ToastRecord[]>([]);
  const [mounted, setMounted] = useState(false);
  const timers = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  // Mount-gate the render so the server outputs nothing and the client only
  // attaches this tree AFTER hydration. Some accessibility browser extensions
  // (e.g. anything that injects `hl-aria-live-message-container`) hijack any
  // `aria-live` region in the server HTML before React hydrates, which
  // produces a hydration mismatch. Rendering post-mount sidesteps that
  // entirely because there is no server HTML for the extension to patch.
  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    return bus.subscribe(setToasts);
  }, []);

  useEffect(() => {
    // Schedule auto-dismiss for any toast that does not already have a timer.
    const current = timers.current;
    for (const t of toasts) {
      if (current.has(t.id)) continue;
      if (t.duration <= 0) continue;
      const handle = setTimeout(() => {
        bus.dismiss(t.id);
        current.delete(t.id);
      }, t.duration);
      current.set(t.id, handle);
    }
    // Clean up timers for toasts that no longer exist.
    for (const [id, handle] of current.entries()) {
      if (!toasts.find((t) => t.id === id)) {
        clearTimeout(handle);
        current.delete(id);
      }
    }
  }, [toasts]);

  const dismiss = useCallback((id: string) => {
    bus.dismiss(id);
  }, []);

  const list = useMemo(() => toasts, [toasts]);

  if (!mounted) return null;

  return (
    <ToastCtx.Provider value={api}>
      <div
        aria-live="polite"
        aria-atomic="false"
        // Defensive: if an extension still races us and patches the node,
        // React won't warn and will leave the extension's attrs in place
        // (the live region is ephemeral chrome, not product content).
        suppressHydrationWarning
        className="pointer-events-none fixed inset-x-0 bottom-0 z-[100] flex flex-col items-center gap-2 px-4 pb-4 sm:bottom-4 sm:right-4 sm:left-auto sm:items-end"
      >
        {list.map((t) => (
          <div
            key={t.id}
            role="status"
            className={cn(
              "pointer-events-auto flex w-full max-w-sm items-start gap-3 rounded-lg border p-3 text-sm shadow-elevated animate-slide-up",
              VARIANT_CLASS[t.variant],
            )}
          >
            <span
              className={cn("mt-0.5 flex-shrink-0 [&_svg]:size-4", VARIANT_ICON_CLASS[t.variant])}
            >
              {VARIANT_ICON[t.variant]}
            </span>
            <div className="flex-1">
              <p className="font-medium leading-tight">{t.title}</p>
              {t.description ? (
                <p className="mt-1 text-xs text-muted-foreground">
                  {t.description}
                </p>
              ) : null}
            </div>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={() => dismiss(t.id)}
              aria-label="Dismiss notification"
              className="-mr-1 -mt-1 h-7 w-7"
            >
              <XIcon />
            </Button>
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  );
}
