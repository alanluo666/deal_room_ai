"use client";

/**
 * DealRoomLogo — original brand mark for Deal Room AI.
 *
 * Concept
 * -------
 * A rounded-square "secure room" frame enclosing three horizontal stacked
 * bars of decreasing length. The bars simultaneously read as:
 *   1. structured deal documents (diligence, data room),
 *   2. the right-curved negative space of a "D" (Deal), and
 *   3. layered confidence — long → short — which subtly evokes
 *      analysis / synthesis.
 *
 * A small accent dot in the upper-right of the frame stands in for an
 * AI signal / intelligence indicator without resorting to a robot or a
 * generic sparkle. The mark keeps its indigo gradient across tones; only
 * the wordmark color adapts so the same icon works on both the dark
 * sidebar and the light main canvas.
 *
 * The SVG is self-contained, inline, and dependency-free. A unique
 * gradient id is generated per instance via `useId` so multiple logos
 * can render on the same page without id collisions.
 *
 * Accessibility
 * -------------
 * - When `ariaLabel` is provided the SVG becomes a meaningful image
 *   (`role="img" aria-label="…"`).
 * - Otherwise the SVG is marked `aria-hidden`. In the "full" variant the
 *   visible wordmark already carries the brand name to screen readers.
 *
 * Previewing
 * ----------
 *   import { DealRoomLogo } from "@/components/branding/DealRoomLogo";
 *   <DealRoomLogo />                              // full, light tone
 *   <DealRoomLogo variant="icon" />               // icon only
 *   <DealRoomLogo tone="dark" />                  // dark-sidebar wordmark
 *   <DealRoomLogo className="h-10 gap-3" />       // responsive sizing
 *   <DealRoomLogo variant="icon" ariaLabel="Deal Room AI home" />
 */

import { useId } from "react";

import { cn } from "@/lib/utils";

type Tone = "light" | "dark";
type Variant = "full" | "icon";

interface DealRoomLogoProps {
  /** "full" = icon + wordmark, "icon" = icon only. */
  variant?: Variant;
  /** "light" = wordmark slate-900 (on light canvas),
   *  "dark"  = wordmark slate-100 (on dark sidebar). */
  tone?: Tone;
  /** Sizing / spacing pass-through. Prefer `h-* w-*` for the icon and
   *  `gap-*`/`text-*` when styling the full lockup. */
  className?: string;
  /** If provided, the SVG becomes a meaningful image with this label.
   *  If omitted, the mark is decorative. */
  ariaLabel?: string;
}

export function DealRoomLogo({
  variant = "full",
  tone = "light",
  className,
  ariaLabel,
}: DealRoomLogoProps) {
  const wordmarkColor = tone === "dark" ? "text-slate-100" : "text-slate-900";
  const aiChipStyles =
    tone === "dark"
      ? "bg-white/10 text-indigo-200 ring-1 ring-inset ring-white/10"
      : "bg-primary/10 text-primary ring-1 ring-inset ring-primary/15";

  if (variant === "icon") {
    return (
      <DealRoomMark
        className={cn("h-7 w-7", className)}
        ariaLabel={ariaLabel}
      />
    );
  }

  return (
    <span
      className={cn("inline-flex items-center gap-2.5", className)}
      aria-label={ariaLabel}
      role={ariaLabel ? "img" : undefined}
    >
      <DealRoomMark className="h-7 w-7 shrink-0" />
      <span
        className={cn(
          "inline-flex items-baseline gap-1.5 text-[15px] font-semibold leading-none tracking-tight",
          wordmarkColor,
        )}
      >
        <span>Deal Room</span>
        <span
          className={cn(
            "rounded-[4px] px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-[0.14em]",
            aiChipStyles,
          )}
        >
          AI
        </span>
      </span>
    </span>
  );
}

interface DealRoomMarkProps {
  className?: string;
  ariaLabel?: string;
}

/**
 * Pure icon mark. 32×32 viewBox, crisp from favicon (16px) through hero
 * sizes (64–80px). Consumers control size via Tailwind `h-*`/`w-*`.
 */
function DealRoomMark({ className, ariaLabel }: DealRoomMarkProps) {
  const uid = useId().replace(/:/g, "");
  const gradId = `drai-grad-${uid}`;
  const glossId = `drai-gloss-${uid}`;

  const labelled = Boolean(ariaLabel);

  return (
    <svg
      viewBox="0 0 32 32"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      role={labelled ? "img" : undefined}
      aria-label={ariaLabel}
      aria-hidden={labelled ? undefined : true}
      focusable="false"
    >
      <defs>
        <linearGradient
          id={gradId}
          x1="4"
          y1="2"
          x2="28"
          y2="30"
          gradientUnits="userSpaceOnUse"
        >
          {/* indigo-400 → indigo-600 */}
          <stop offset="0%" stopColor="#818CF8" />
          <stop offset="100%" stopColor="#4F46E5" />
        </linearGradient>
        <linearGradient
          id={glossId}
          x1="6"
          y1="2"
          x2="6"
          y2="16"
          gradientUnits="userSpaceOnUse"
        >
          <stop offset="0%" stopColor="#ffffff" stopOpacity="0.18" />
          <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
        </linearGradient>
      </defs>

      {/* Secure "room" frame */}
      <rect
        x="2"
        y="2"
        width="28"
        height="28"
        rx="7"
        fill={`url(#${gradId})`}
      />
      {/* Subtle top gloss for depth */}
      <rect
        x="2"
        y="2"
        width="28"
        height="28"
        rx="7"
        fill={`url(#${glossId})`}
      />

      {/* Structured document lines — decreasing length suggests D/analysis */}
      <rect
        x="8"
        y="10.5"
        width="14"
        height="2.25"
        rx="1.125"
        fill="#ffffff"
      />
      <rect
        x="8"
        y="15.25"
        width="11"
        height="2.25"
        rx="1.125"
        fill="#ffffff"
        fillOpacity="0.82"
      />
      <rect
        x="8"
        y="20"
        width="7.5"
        height="2.25"
        rx="1.125"
        fill="#ffffff"
        fillOpacity="0.58"
      />

      {/* AI signal dot */}
      <circle cx="24" cy="9" r="1.6" fill="#ffffff" />
    </svg>
  );
}
