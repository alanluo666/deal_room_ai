"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import type { ReactNode } from "react";

import { DealRoomLogo } from "@/components/branding/DealRoomLogo";
import { useLogout, useUser } from "@/lib/auth";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu";
import { ChevronDownIcon, LogOutIcon, UserIcon } from "../icons";
import { toast } from "../ui/toaster";

interface TopbarProps {
  breadcrumbs?: ReactNode;
}

export function Topbar({ breadcrumbs }: TopbarProps) {
  const router = useRouter();
  const { data: user } = useUser();
  const logout = useLogout();

  const onLogout = async () => {
    try {
      await logout.mutateAsync();
      router.push("/login");
      router.refresh();
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Could not sign out.";
      toast.error("Sign out failed", { description: message });
    }
  };

  const userInitial = user?.email?.trim().charAt(0).toUpperCase() ?? "?";

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-4 border-b border-border bg-background/80 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/70 lg:px-8">
      <Link
        href="/deal-rooms"
        aria-label="Deal Room AI — Home"
        className="flex items-center lg:hidden focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-md"
      >
        <DealRoomLogo />
      </Link>

      <div className="flex min-w-0 flex-1 items-center gap-2 text-sm text-muted-foreground">
        {breadcrumbs}
      </div>

      <DropdownMenu>
        <DropdownMenuTrigger
          aria-label="Account menu"
          className="inline-flex h-9 items-center gap-2 rounded-full border border-border bg-card pl-1 pr-2.5 text-sm font-medium text-foreground shadow-soft transition-colors hover:bg-accent"
        >
          <span
            aria-hidden="true"
            className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-indigo-600 text-xs font-semibold text-white"
          >
            {user ? userInitial : <UserIcon className="h-3.5 w-3.5" />}
          </span>
          <span className="hidden max-w-[12rem] truncate sm:inline">
            {user?.email ?? "Account"}
          </span>
          <ChevronDownIcon
            className="h-3.5 w-3.5 text-muted-foreground"
            aria-hidden="true"
          />
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-60">
          <DropdownMenuLabel>Signed in</DropdownMenuLabel>
          <div className="truncate px-2.5 pb-1.5 text-xs text-muted-foreground">
            {user?.email ?? "—"}
          </div>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={onLogout} disabled={logout.isPending}>
            <LogOutIcon className="h-4 w-4" aria-hidden="true" />
            {logout.isPending ? "Signing out…" : "Sign out"}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </header>
  );
}

interface BreadcrumbsProps {
  items: Array<{ label: string; href?: string }>;
}

export function Breadcrumbs({ items }: BreadcrumbsProps) {
  return (
    <nav aria-label="Breadcrumb" className="flex min-w-0 items-center gap-1.5">
      {items.map((item, idx) => {
        const isLast = idx === items.length - 1;
        return (
          <span
            key={`${item.label}-${idx}`}
            className="flex min-w-0 items-center gap-1.5"
          >
            {item.href && !isLast ? (
              <Link
                href={item.href}
                className="truncate text-muted-foreground hover:text-foreground hover:underline"
              >
                {item.label}
              </Link>
            ) : (
              <span
                aria-current={isLast ? "page" : undefined}
                className="truncate font-medium text-foreground"
              >
                {item.label}
              </span>
            )}
            {isLast ? null : (
              <span aria-hidden="true" className="text-muted-foreground/60">
                /
              </span>
            )}
          </span>
        );
      })}
    </nav>
  );
}
