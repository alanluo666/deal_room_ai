"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ButtonHTMLAttributes,
  type HTMLAttributes,
  type ReactNode,
} from "react";

import { cn } from "@/lib/utils";

/**
 * Lightweight dropdown-menu with a shadcn-compatible surface API (no `asChild`
 * trigger passthrough). Supports click-outside, Escape-to-close, and keyboard
 * activation of items. Menu opens below-right of the trigger by default;
 * override alignment via `align` prop on `DropdownMenuContent`.
 */

interface DropdownCtx {
  open: boolean;
  setOpen: (next: boolean) => void;
  triggerRef: React.RefObject<HTMLButtonElement | null>;
}

const DropdownContext = createContext<DropdownCtx | null>(null);

function useDropdown(component: string) {
  const ctx = useContext(DropdownContext);
  if (!ctx) throw new Error(`<${component}> must be inside <DropdownMenu>`);
  return ctx;
}

export function DropdownMenu({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const value = useMemo(() => ({ open, setOpen, triggerRef }), [open]);
  return (
    <DropdownContext.Provider value={value}>
      <div className="relative inline-flex">{children}</div>
    </DropdownContext.Provider>
  );
}

export function DropdownMenuTrigger({
  className,
  children,
  onClick,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement>) {
  const { open, setOpen, triggerRef } = useDropdown("DropdownMenuTrigger");
  return (
    <button
      ref={triggerRef}
      type="button"
      aria-haspopup="menu"
      aria-expanded={open}
      data-state={open ? "open" : "closed"}
      onClick={(event) => {
        setOpen(!open);
        onClick?.(event);
      }}
      className={cn("inline-flex", className)}
      {...props}
    >
      {children}
    </button>
  );
}

interface DropdownMenuContentProps extends HTMLAttributes<HTMLDivElement> {
  align?: "start" | "end";
  sideOffset?: number;
}

export function DropdownMenuContent({
  align = "end",
  sideOffset = 6,
  className,
  children,
  ...props
}: DropdownMenuContentProps) {
  const { open, setOpen, triggerRef } = useDropdown("DropdownMenuContent");
  const contentRef = useRef<HTMLDivElement | null>(null);

  const close = useCallback(() => setOpen(false), [setOpen]);

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: MouseEvent) => {
      const target = event.target as Node;
      if (
        contentRef.current?.contains(target) ||
        triggerRef.current?.contains(target)
      ) {
        return;
      }
      close();
    };
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        close();
        triggerRef.current?.focus();
      }
    };
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open, close, triggerRef]);

  if (!open) return null;

  return (
    <div
      ref={contentRef}
      role="menu"
      style={{ marginTop: sideOffset }}
      className={cn(
        "absolute top-full z-40 min-w-[10rem] overflow-hidden rounded-md border border-border bg-popover p-1 text-popover-foreground shadow-elevated animate-slide-up",
        align === "end" ? "right-0 origin-top-right" : "left-0 origin-top-left",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}

interface DropdownMenuItemProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  destructive?: boolean;
  inset?: boolean;
}

export function DropdownMenuItem({
  className,
  destructive,
  inset,
  children,
  onClick,
  ...props
}: DropdownMenuItemProps) {
  const { setOpen } = useDropdown("DropdownMenuItem");
  return (
    <button
      type="button"
      role="menuitem"
      onClick={(event) => {
        onClick?.(event);
        if (!event.defaultPrevented) setOpen(false);
      }}
      className={cn(
        "flex w-full cursor-pointer select-none items-center gap-2 rounded-sm px-2.5 py-2 text-sm outline-none transition-colors",
        "focus-visible:bg-accent focus-visible:text-accent-foreground hover:bg-accent hover:text-accent-foreground",
        "disabled:pointer-events-none disabled:opacity-50",
        destructive && "text-destructive hover:bg-destructive/10 hover:text-destructive",
        inset && "pl-8",
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}

export function DropdownMenuLabel({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "px-2.5 py-1.5 text-xs font-medium uppercase tracking-wide text-muted-foreground",
        className,
      )}
      {...props}
    />
  );
}

export function DropdownMenuSeparator({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      role="separator"
      className={cn("-mx-1 my-1 h-px bg-border", className)}
      {...props}
    />
  );
}
