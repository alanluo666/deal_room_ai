"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useId,
  useMemo,
  useRef,
  type HTMLAttributes,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";

import { cn } from "@/lib/utils";

import { Button } from "./button";
import { XIcon } from "../icons";

/**
 * Hand-rolled Dialog with a shadcn-compatible API:
 *
 *   <Dialog open={o} onOpenChange={setO}>
 *     <DialogContent>
 *       <DialogHeader>
 *         <DialogTitle>...</DialogTitle>
 *         <DialogDescription>...</DialogDescription>
 *       </DialogHeader>
 *       ...body...
 *       <DialogFooter>...</DialogFooter>
 *     </DialogContent>
 *   </Dialog>
 *
 * Features: portal to <body>, escape-to-close, backdrop click, scroll lock,
 * autofocus on open, labelled-by wiring via context. Not a full focus trap —
 * we intentionally keep this lightweight until shadcn/Radix lands.
 */

interface DialogCtx {
  open: boolean;
  onOpenChange: (next: boolean) => void;
  labelId: string;
  descriptionId: string;
}

const DialogContext = createContext<DialogCtx | null>(null);

function useDialog(component: string) {
  const ctx = useContext(DialogContext);
  if (!ctx) throw new Error(`<${component}> must be inside <Dialog>`);
  return ctx;
}

export interface DialogProps {
  open: boolean;
  onOpenChange: (next: boolean) => void;
  children?: ReactNode;
}

export function Dialog({ open, onOpenChange, children }: DialogProps) {
  const labelId = useId();
  const descriptionId = useId();

  useEffect(() => {
    if (!open) return;
    const original = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = original;
    };
  }, [open]);

  const value = useMemo<DialogCtx>(
    () => ({ open, onOpenChange, labelId, descriptionId }),
    [open, onOpenChange, labelId, descriptionId],
  );

  return <DialogContext.Provider value={value}>{children}</DialogContext.Provider>;
}

interface DialogContentProps extends HTMLAttributes<HTMLDivElement> {
  showClose?: boolean;
}

export function DialogContent({
  className,
  children,
  showClose = true,
  ...props
}: DialogContentProps) {
  const { open, onOpenChange, labelId, descriptionId } = useDialog("DialogContent");
  const contentRef = useRef<HTMLDivElement | null>(null);

  const close = useCallback(() => onOpenChange(false), [onOpenChange]);

  useEffect(() => {
    if (!open) return;
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") close();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open, close]);

  useEffect(() => {
    if (!open) return;
    const el = contentRef.current;
    if (!el) return;
    const focusable = el.querySelector<HTMLElement>(
      "[data-autofocus], input:not([disabled]), button:not([disabled]), [tabindex]:not([tabindex='-1'])",
    );
    focusable?.focus();
  }, [open]);

  if (!open || typeof document === "undefined") return null;

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="presentation"
    >
      <div
        className="absolute inset-0 bg-foreground/40 animate-fade-in"
        onClick={close}
        aria-hidden="true"
      />
      <div
        ref={contentRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={labelId}
        aria-describedby={descriptionId}
        className={cn(
          "relative z-10 w-full max-w-lg animate-zoom-in rounded-lg border border-border bg-popover p-6 text-popover-foreground shadow-elevated",
          className,
        )}
        {...props}
      >
        {children}
        {showClose ? (
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={close}
            aria-label="Close dialog"
            className="absolute right-3 top-3"
          >
            <XIcon />
          </Button>
        ) : null}
      </div>
    </div>,
    document.body,
  );
}

export function DialogHeader({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("flex flex-col gap-1.5 text-left", className)}
      {...props}
    />
  );
}

export function DialogFooter({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end",
        className,
      )}
      {...props}
    />
  );
}

export function DialogTitle({
  className,
  ...props
}: HTMLAttributes<HTMLHeadingElement>) {
  const { labelId } = useDialog("DialogTitle");
  return (
    <h2
      id={labelId}
      className={cn("text-base font-semibold text-foreground", className)}
      {...props}
    />
  );
}

export function DialogDescription({
  className,
  ...props
}: HTMLAttributes<HTMLParagraphElement>) {
  const { descriptionId } = useDialog("DialogDescription");
  return (
    <p
      id={descriptionId}
      className={cn("text-sm text-muted-foreground", className)}
      {...props}
    />
  );
}
