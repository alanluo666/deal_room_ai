import { forwardRef, type HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

/**
 * Card keeps the original contract from the legacy `components/ui.tsx`:
 * a single padded surface. Callers pass children directly; internal padding
 * and radius are baked in. Override padding with `className="p-0"` when
 * composing a header/footer manually (see DocumentList).
 */
export const Card = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  function Card({ className, ...props }, ref) {
    return (
      <div
        ref={ref}
        className={cn(
          "rounded-lg border border-border bg-card p-5 text-card-foreground shadow-soft",
          className,
        )}
        {...props}
      />
    );
  },
);
