import clsx, { type ClassValue } from "clsx";

/**
 * Small class-name helper in the spirit of shadcn's `cn`, but without the
 * `tailwind-merge` dependency. We rely on declaration order at call sites to
 * let later classes win; this is fine because every component in the kit
 * applies its base classes first and spreads the consumer's `className` after.
 */
export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs);
}

export function formatRelativeTime(input: string | Date): string {
  const date = typeof input === "string" ? new Date(input) : input;
  const now = new Date();
  const diffMs = date.getTime() - now.getTime();
  const diffSec = Math.round(diffMs / 1000);
  const absSec = Math.abs(diffSec);

  const units: Array<[Intl.RelativeTimeFormatUnit, number]> = [
    ["year", 60 * 60 * 24 * 365],
    ["month", 60 * 60 * 24 * 30],
    ["week", 60 * 60 * 24 * 7],
    ["day", 60 * 60 * 24],
    ["hour", 60 * 60],
    ["minute", 60],
    ["second", 1],
  ];

  const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
  for (const [unit, secondsInUnit] of units) {
    if (absSec >= secondsInUnit || unit === "second") {
      const value = Math.round(diffSec / secondsInUnit);
      return rtf.format(value, unit);
    }
  }
  return "just now";
}
