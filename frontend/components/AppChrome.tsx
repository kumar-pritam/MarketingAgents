"use client";

import Link from "next/link";
import type { Route } from "next";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { NavBar } from "./NavBar";
import { usePageTracking } from "../hooks/usePageTracking";

export function AppChrome({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const isAuthShell = pathname.startsWith("/auth");

  usePageTracking();

  if (isAuthShell) {
    return <main className="auth-page-shell">{children}</main>;
  }

  return (
    <>
      <NavBar />
      <main className="container">{children}</main>
      <footer className="footer">
        <div className="container footer-inner">
          <div className="footer-brand">
            <strong>MarketingAgents.ai</strong>
            <span>The AI Marketing OS for brand-led teams</span>
          </div>
          <div className="footer-links">
            <Link href={"/" as Route}>Home</Link>
            <Link href={"/workspaces" as Route}>Brand Workspace</Link>
            <Link href={"/agents" as Route}>Agent Studio</Link>
            <Link href={"/history" as Route}>Run History</Link>
            <a href="mailto:hello@marketingagents.ai">Contact</a>
          </div>
        </div>
      </footer>
    </>
  );
}
