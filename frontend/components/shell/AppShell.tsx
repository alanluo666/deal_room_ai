"use client";

import type { ReactNode } from "react";

import { SidebarNav } from "./SidebarNav";
import { Topbar } from "./Topbar";

interface AppShellProps {
  children: ReactNode;
  breadcrumbs?: ReactNode;
}

export function AppShell({ children, breadcrumbs }: AppShellProps) {
  return (
    <div className="flex min-h-screen bg-muted/30">
      <SidebarNav />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar breadcrumbs={breadcrumbs} />
        <main className="flex-1 px-4 py-6 lg:px-10 lg:py-10">{children}</main>
      </div>
    </div>
  );
}
