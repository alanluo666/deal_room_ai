"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import type { ReactNode } from "react";

import { useLogout, useUser } from "@/lib/auth";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu";
import {
  ChevronDownIcon,
  LogOutIcon,
  SparklesIcon,
  UserIcon,
} from "../icons";
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

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-4 border-b border-border bg-background/95 px-4 backdrop-blur-sm lg:px-6">
      <Link
        href="/deal-rooms"
        className="flex items-center gap-2 font-semibold tracking-tight lg:hidden"
      >
        <span className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-primary-foreground">
          <SparklesIcon className="h-4 w-4" />
        </span>
        Deal Room AI
      </Link>

      <div className="flex min-w-0 flex-1 items-center gap-2 text-sm text-muted-foreground">
        {breadcrumbs}
      </div>

      <DropdownMenu>
        <DropdownMenuTrigger
          aria-label="Account menu"
          className="inline-flex h-9 items-center gap-2 rounded-md px-2 text-sm font-medium text-foreground hover:bg-accent"
        >
          <span
            aria-hidden="true"
            className="flex h-7 w-7 items-center justify-center rounded-full bg-muted text-muted-foreground"
          >
            <UserIcon className="h-4 w-4" />
          </span>
          <span className="hidden max-w-[12rem] truncate sm:inline">
            {user?.email ?? "Account"}
          </span>
          <ChevronDownIcon
            className="h-4 w-4 text-muted-foreground"
            aria-hidden="true"
          />
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          <DropdownMenuLabel>Signed in</DropdownMenuLabel>
          <div className="truncate px-2.5 pb-1.5 text-xs text-muted-foreground">
            {user?.email ?? "—"}
          </div>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={onLogout} disabled={logout.isPending}>
            <LogOutIcon className="h-4 w-4" />
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
          <span key={`${item.label}-${idx}`} className="flex min-w-0 items-center gap-1.5">
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
