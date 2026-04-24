"use client";

import {
  createContext,
  useCallback,
  useContext,
  useId,
  useMemo,
  useRef,
  useState,
  type HTMLAttributes,
  type ReactNode,
} from "react";

import { cn } from "@/lib/utils";

/**
 * Hand-rolled Tabs with a public API that mirrors shadcn/ui so a future
 * swap to `@radix-ui/react-tabs` is a drop-in replacement. Supports
 * controlled and uncontrolled modes, keyboard left/right to change tabs,
 * and proper ARIA roles.
 *
 * Two visual variants are supported:
 * - "pill"      (default) — segmented pill bar, backed by `bg-muted`.
 * - "underline"           — executive style, transparent row with an
 *                           accent underline on the active tab.
 *
 * The variant is propagated from `<TabsList>` to its triggers via context
 * so `<TabsTrigger>` does not have to repeat it.
 */

type TabsVariant = "pill" | "underline";

interface TabsContextValue {
  value: string;
  setValue: (next: string) => void;
  idBase: string;
  orientation: "horizontal" | "vertical";
  variant: TabsVariant;
}

const TabsContext = createContext<TabsContextValue | null>(null);

function useTabs(component: string) {
  const ctx = useContext(TabsContext);
  if (!ctx) {
    throw new Error(`<${component}> must be rendered inside <Tabs>`);
  }
  return ctx;
}

interface TabsProps extends Omit<HTMLAttributes<HTMLDivElement>, "onChange"> {
  value?: string;
  defaultValue?: string;
  onValueChange?: (value: string) => void;
  orientation?: "horizontal" | "vertical";
  variant?: TabsVariant;
  children?: ReactNode;
}

export function Tabs({
  value,
  defaultValue,
  onValueChange,
  orientation = "horizontal",
  variant = "pill",
  className,
  children,
  ...props
}: TabsProps) {
  const [internal, setInternal] = useState(defaultValue ?? "");
  const current = value ?? internal;
  const idBase = useId();

  const setValue = useCallback(
    (next: string) => {
      if (value === undefined) setInternal(next);
      onValueChange?.(next);
    },
    [value, onValueChange],
  );

  const ctx = useMemo<TabsContextValue>(
    () => ({ value: current, setValue, idBase, orientation, variant }),
    [current, setValue, idBase, orientation, variant],
  );

  return (
    <TabsContext.Provider value={ctx}>
      <div
        data-orientation={orientation}
        data-variant={variant}
        className={cn(
          orientation === "vertical" ? "flex gap-6" : "flex flex-col gap-4",
          className,
        )}
        {...props}
      >
        {children}
      </div>
    </TabsContext.Provider>
  );
}

interface TabsListProps extends HTMLAttributes<HTMLDivElement> {
  children?: ReactNode;
}

export function TabsList({ className, children, ...props }: TabsListProps) {
  const { orientation, variant } = useTabs("TabsList");

  const variantCls =
    variant === "underline"
      ? "h-auto gap-1 rounded-none border-b border-border bg-transparent p-0 text-muted-foreground"
      : "gap-1 rounded-lg bg-muted p-1 text-muted-foreground";

  return (
    <div
      role="tablist"
      aria-orientation={orientation}
      className={cn(
        "inline-flex items-center",
        orientation === "vertical" ? "flex-col" : "flex-row",
        variantCls,
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}

interface TabsTriggerProps
  extends Omit<HTMLAttributes<HTMLButtonElement>, "onClick"> {
  value: string;
  disabled?: boolean;
  children?: ReactNode;
}

export function TabsTrigger({
  value,
  disabled,
  className,
  children,
  ...props
}: TabsTriggerProps) {
  const {
    value: current,
    setValue,
    idBase,
    orientation,
    variant,
  } = useTabs("TabsTrigger");
  const active = current === value;
  const triggerRef = useRef<HTMLButtonElement | null>(null);

  const onKeyDown = (event: React.KeyboardEvent<HTMLButtonElement>) => {
    const nextKeys = orientation === "horizontal" ? ["ArrowRight"] : ["ArrowDown"];
    const prevKeys = orientation === "horizontal" ? ["ArrowLeft"] : ["ArrowUp"];
    if (![...nextKeys, ...prevKeys, "Home", "End"].includes(event.key)) return;
    event.preventDefault();

    const parent = triggerRef.current?.parentElement;
    if (!parent) return;
    const triggers = Array.from(
      parent.querySelectorAll<HTMLButtonElement>("[role='tab']:not([disabled])"),
    );
    const currentIndex = triggers.indexOf(triggerRef.current as HTMLButtonElement);
    let target = currentIndex;
    if (nextKeys.includes(event.key)) target = (currentIndex + 1) % triggers.length;
    else if (prevKeys.includes(event.key))
      target = (currentIndex - 1 + triggers.length) % triggers.length;
    else if (event.key === "Home") target = 0;
    else if (event.key === "End") target = triggers.length - 1;

    const next = triggers[target];
    if (next) {
      next.focus();
      next.click();
    }
  };

  const pillCls = cn(
    "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium transition-all",
    "disabled:pointer-events-none disabled:opacity-50",
    active
      ? "bg-background text-foreground shadow-soft"
      : "hover:text-foreground",
  );

  const underlineCls = cn(
    "group relative inline-flex items-center justify-center gap-2 whitespace-nowrap border-b-2 px-3 py-2.5 text-sm font-medium transition-colors",
    "disabled:pointer-events-none disabled:opacity-50",
    active
      ? "border-primary text-foreground"
      : "border-transparent hover:text-foreground",
  );

  return (
    <button
      ref={triggerRef}
      role="tab"
      type="button"
      id={`${idBase}-trigger-${value}`}
      aria-controls={`${idBase}-content-${value}`}
      aria-selected={active}
      tabIndex={active ? 0 : -1}
      disabled={disabled}
      onClick={() => setValue(value)}
      onKeyDown={onKeyDown}
      className={cn(variant === "underline" ? underlineCls : pillCls, className)}
      {...props}
    >
      {children}
    </button>
  );
}

interface TabsContentProps extends HTMLAttributes<HTMLDivElement> {
  value: string;
  children?: ReactNode;
  forceMount?: boolean;
}

export function TabsContent({
  value,
  forceMount,
  className,
  children,
  ...props
}: TabsContentProps) {
  const { value: current, idBase } = useTabs("TabsContent");
  const active = current === value;
  if (!active && !forceMount) return null;
  return (
    <div
      role="tabpanel"
      id={`${idBase}-content-${value}`}
      aria-labelledby={`${idBase}-trigger-${value}`}
      hidden={!active}
      className={cn("focus-visible:outline-none", className)}
      {...props}
    >
      {children}
    </div>
  );
}
