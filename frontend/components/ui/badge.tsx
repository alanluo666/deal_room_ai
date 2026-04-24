import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export type BadgeVariant =
  | "default"
  | "secondary"
  | "success"
  | "warning"
  | "destructive"
  | "outline";

const VARIANTS: Record<BadgeVariant, string> = {
  default: "border-transparent bg-primary/10 text-primary",
  secondary: "border-transparent bg-secondary text-secondary-foreground",
  success:
    "border-transparent bg-success/15 text-success dark:bg-success/20",
  warning:
    "border-transparent bg-warning/20 text-warning-foreground dark:bg-warning/25 dark:text-warning",
  destructive:
    "border-transparent bg-destructive/10 text-destructive",
  outline: "border-border bg-transparent text-foreground",
};

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
}

export function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium capitalize",
        VARIANTS[variant],
        className,
      )}
      {...props}
    />
  );
}
