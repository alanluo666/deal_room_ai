"use client";

/**
 * DealRoomLogo — brand mark for Deal Room AI.
 *
 * Concept
 * -------
 * An abstract open-room / open-book frame rendered as two mirrored
 * panels joined by a central spine. The left panel shows three stacked
 * document lines (diligence materials); the right panel shows two
 * ascending analytics bars (AI-driven analysis). The outline uses an
 * indigo-to-blue linear gradient (`#4F46E5 → #2563EB → #3B82F6`), the
 * document lines render in slate-900, and the analytics bars pick up
 * the same blue family as the stroke. The white panel fills keep the
 * mark crisp on both light canvases and dark navy backgrounds.
 *
 * Public API is unchanged from the previous component so existing
 * imports keep working:
 *
 *   <DealRoomLogo />                        // full, light tone
 *   <DealRoomLogo tone="dark" />            // full, white wordmark
 *   <DealRoomLogo variant="icon" />         // icon only
 *   <DealRoomLogo className="h-10 w-10" />  // pass sizing through
 *
 * Accessibility
 * -------------
 * `ariaLabel` defaults to "Deal Room AI". In the icon variant it is
 * applied to the SVG as `role="img" aria-label="…"`. In the full
 * variant the visible wordmark carries the brand name and the SVG
 * stays decorative (`aria-hidden`).
 */

import * as React from "react";

type DealRoomLogoProps = {
  variant?: "full" | "icon";
  tone?: "light" | "dark";
  className?: string;
  iconClassName?: string;
  wordmarkClassName?: string;
  ariaLabel?: string;
};

function DealRoomMark({
  className,
  ariaLabel,
}: {
  className?: string;
  ariaLabel?: string;
}) {
  const gradientId = React.useId();

  return (
    <svg
      viewBox="0 0 64 64"
      className={className}
      role={ariaLabel ? "img" : undefined}
      aria-label={ariaLabel}
      aria-hidden={ariaLabel ? undefined : true}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      focusable="false"
    >
      <defs>
        <linearGradient
          id={gradientId}
          x1="8"
          y1="10"
          x2="56"
          y2="54"
          gradientUnits="userSpaceOnUse"
        >
          <stop offset="0%" stopColor="#4F46E5" />
          <stop offset="55%" stopColor="#2563EB" />
          <stop offset="100%" stopColor="#3B82F6" />
        </linearGradient>
      </defs>

      {/* Outer "open room" / open-book frame */}
      <path
        d="M10 18.5L28 12V52L10 46.5V18.5Z"
        fill="white"
        stroke={`url(#${gradientId})`}
        strokeWidth="3.5"
        strokeLinejoin="round"
      />
      <path
        d="M36 12L54 18.5V46.5L36 52V12Z"
        fill="white"
        stroke={`url(#${gradientId})`}
        strokeWidth="3.5"
        strokeLinejoin="round"
      />

      {/* Center spine */}
      <path
        d="M32 11V53"
        stroke={`url(#${gradientId})`}
        strokeWidth="3.5"
        strokeLinecap="round"
      />

      {/* Left document lines */}
      <rect
        x="16.5"
        y="24"
        width="11.5"
        height="3.5"
        rx="1.25"
        fill="#1E293B"
      />
      <rect
        x="16.5"
        y="31"
        width="11.5"
        height="3.5"
        rx="1.25"
        fill="#1E293B"
        opacity="0.9"
      />
      <rect
        x="16.5"
        y="38"
        width="8"
        height="3.5"
        rx="1.25"
        fill="#1E293B"
        opacity="0.8"
      />

      {/* Right analytics bars */}
      <rect x="40.5" y="39" width="4.5" height="9" rx="1.5" fill="#3B82F6" />
      <rect
        x="47"
        y="31.5"
        width="4.5"
        height="16.5"
        rx="1.5"
        fill="#2563EB"
      />
    </svg>
  );
}

export function DealRoomLogo({
  variant = "full",
  tone = "light",
  className,
  iconClassName,
  wordmarkClassName,
  ariaLabel = "Deal Room AI",
}: DealRoomLogoProps) {
  const isDark = tone === "dark";

  const roomText = isDark ? "text-white" : "text-slate-950";
  const aiText = "text-blue-600";
  const defaultWordmark = "font-semibold tracking-tight";

  if (variant === "icon") {
    return (
      <DealRoomMark
        className={iconClassName ?? className ?? "h-9 w-9"}
        ariaLabel={ariaLabel}
      />
    );
  }

  return (
    <div
      className={className ?? "inline-flex items-center gap-3"}
      aria-label={ariaLabel}
    >
      <DealRoomMark className={iconClassName ?? "h-10 w-10 shrink-0"} />
      <div
        className={
          wordmarkClassName ??
          `${defaultWordmark} ${roomText} text-2xl leading-none`
        }
      >
        <span>Deal Room </span>
        <span className={aiText}>AI</span>
      </div>
    </div>
  );
}

export default DealRoomLogo;
