"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { DealRoomLogo } from "@/components/branding/DealRoomLogo";
import { cn } from "@/lib/utils";

import { Building2Icon, FileTextIcon, SettingsIcon } from "../icons";

/**
 * Always-dark navy sidebar (independent of OS color scheme), matching the
 * premium B2B SaaS pattern used by Linear/Vercel/Notion where the nav rail
 * stays dark even when the main canvas is light. Uses hardcoded Tailwind
 * slate colors intentionally — the rest of the app still follows the HSL
 * token system and OS-driven dark mode.
 */

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  disabled?: boolean;
}

const PRIMARY_NAV: NavItem[] = [
  { label: "Deal rooms", href: "/deal-rooms", icon: Building2Icon },
  { label: "Findings", href: "#findings", icon: FileTextIcon, disabled: true },
  { label: "Settings", href: "#settings", icon: SettingsIcon, disabled: true },
];

export function SidebarNav() {
  const pathname = usePathname();

  return (
    <aside
      aria-label="Sidebar"
      className="hidden w-60 shrink-0 flex-col border-r border-slate-800/80 bg-slate-950 text-slate-200 lg:flex"
    >
      <Link
        href="/deal-rooms"
        aria-label="Deal Room AI — Home"
        className="flex h-14 items-center border-b border-slate-800/80 px-5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        <DealRoomLogo
          tone="dark"
          className="inline-flex items-center gap-2.5"
          iconClassName="h-7 w-7 shrink-0"
          wordmarkClassName="font-semibold tracking-tight text-white text-[15px] leading-none"
        />
      </Link>

      <div className="px-3 pt-5">
        <p className="px-2 pb-2 text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">
          Workspace
        </p>
        <nav aria-label="Primary" className="flex flex-col gap-0.5">
          {PRIMARY_NAV.map((item) => {
            const Icon = item.icon;
            const active =
              !item.disabled &&
              (pathname === item.href || pathname.startsWith(`${item.href}/`));
            const base =
              "group flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm font-medium transition-colors";

            if (item.disabled) {
              return (
                <span
                  key={item.href}
                  aria-disabled="true"
                  className={cn(
                    base,
                    "cursor-not-allowed text-slate-500",
                  )}
                  title="Coming soon"
                >
                  <Icon className="h-4 w-4" aria-hidden="true" />
                  {item.label}
                  <span className="ml-auto rounded-full border border-slate-700/80 bg-slate-900/60 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-400">
                    Soon
                  </span>
                </span>
              );
            }
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  base,
                  active
                    ? "bg-white/5 text-white shadow-[inset_2px_0_0_0_hsl(var(--primary))]"
                    : "text-slate-300 hover:bg-white/5 hover:text-white",
                )}
              >
                <Icon
                  className={cn(
                    "h-4 w-4 shrink-0 transition-colors",
                    active
                      ? "text-indigo-400"
                      : "text-slate-400 group-hover:text-slate-200",
                  )}
                  aria-hidden="true"
                />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="mt-auto border-t border-slate-800/80 px-5 py-4">
        <div className="flex items-center gap-2.5">
          <DealRoomLogo
            variant="icon"
            tone="dark"
            className="h-6 w-6 shrink-0"
          />
          <div className="min-w-0 leading-tight">
            <p className="truncate text-xs font-semibold text-slate-200">
              Deal Room AI
            </p>
            <p className="truncate text-[11px] text-slate-500">
              Due diligence workspace
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
}
