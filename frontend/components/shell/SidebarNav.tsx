"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

import {
  Building2Icon,
  FileTextIcon,
  SettingsIcon,
  SparklesIcon,
} from "../icons";

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
    <aside className="hidden w-60 shrink-0 flex-col border-r border-border bg-card/50 lg:flex">
      <Link
        href="/deal-rooms"
        className="flex h-14 items-center gap-2 border-b border-border px-5 font-semibold tracking-tight"
      >
        <span
          aria-hidden="true"
          className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground shadow-soft"
        >
          <SparklesIcon className="h-4 w-4" />
        </span>
        Deal Room AI
      </Link>
      <nav aria-label="Primary" className="flex flex-col gap-0.5 p-3">
        {PRIMARY_NAV.map((item) => {
          const Icon = item.icon;
          const active =
            !item.disabled &&
            (pathname === item.href || pathname.startsWith(`${item.href}/`));
          const base =
            "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors";
          if (item.disabled) {
            return (
              <span
                key={item.href}
                aria-disabled="true"
                className={cn(
                  base,
                  "cursor-not-allowed text-muted-foreground/60",
                )}
                title="Coming soon"
              >
                <Icon className="h-4 w-4" aria-hidden="true" />
                {item.label}
                <span className="ml-auto rounded-full bg-muted px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-muted-foreground">
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
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground hover:bg-accent/60 hover:text-foreground",
              )}
            >
              <Icon className="h-4 w-4" aria-hidden="true" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="mt-auto border-t border-border p-4 text-xs text-muted-foreground">
        <p className="font-medium text-foreground">Deal Room AI</p>
        <p>AI-powered due diligence workspace.</p>
      </div>
    </aside>
  );
}
