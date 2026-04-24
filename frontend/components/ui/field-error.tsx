import type { ReactNode } from "react";

export function FieldError({ children }: { children?: ReactNode }) {
  if (!children) return null;
  return <p className="text-xs text-destructive">{children}</p>;
}
