"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Route } from "next";
import { useEffect, useRef, useState } from "react";
import { getUserStatus } from "../lib/usageTracking";
import { isLoggedIn, isLoggedInSync, isPro, getUserProfile, getCachedProfile, logout } from "../lib/auth";
import { GetProOverlay } from "./GetProOverlay";
import { AuthModal } from "./GetProOverlay";
import { migrateAnonymousToUser } from "../lib/usageTracking";

const NAV_ITEMS = [
  { href: "/", label: "Home" },
  { href: "/workspaces", label: "Brand Workspace" },
  { href: "/agents", label: "Agent Studio" },
] as const;
const AGENT_CATEGORIES = [
  "Brand Strategy & Health",
  "Channel & Visibility",
  "Competitive Strategy",
  "Content & Campaigns",
  "Content & Creative Generation",
  "Market & Audience Intelligence",
] as const;

export function NavBar() {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [agentsOpen, setAgentsOpen] = useState(false);
  const [showGetPro, setShowGetPro] = useState(false);
  const [showAuth, setShowAuth] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const agentsMenuRef = useRef<HTMLDivElement | null>(null);
  const userMenuRef = useRef<HTMLDivElement | null>(null);
  const [usageStatus, setUsageStatus] = useState<ReturnType<typeof getUserStatus>>({ runs_remaining: 0, runs_limit: 5, tier: "anonymous", runs_used: 0, is_blocked: false, block_reason: null });
  const [loggedIn, setLoggedIn] = useState(false);
  const [pro, setPro] = useState(false);

  useEffect(() => {
    setMounted(true);
    setUsageStatus(getUserStatus());
    setLoggedIn(isLoggedInSync());
    setPro(isPro());
  }, []);

  useEffect(() => {
    function onScroll() {
      setScrolled(window.scrollY > 8);
    }
    onScroll();
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    setMenuOpen(false);
    setAgentsOpen(false);
    if (mounted) {
      setUsageStatus(getUserStatus());
      setLoggedIn(isLoggedInSync());
      setPro(isPro());
    }
  }, [pathname, mounted]);

  useEffect(() => {
    function onPointerDown(event: MouseEvent) {
      if (agentsMenuRef.current && !agentsMenuRef.current.contains(event.target as Node)) {
        setAgentsOpen(false);
      }
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setUserMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", onPointerDown);
    return () => document.removeEventListener("mousedown", onPointerDown);
  }, []);

  const handleLogout = () => {
    logout();
    setLoggedIn(false);
    setUserMenuOpen(false);
    window.location.reload();
  };

  const handleLoginSuccess = () => {
    migrateAnonymousToUser();
    setLoggedIn(true);
    setShowAuth(false);
    setUsageStatus(getUserStatus());
  };

  return (
    <>
      <header className={`nav ${scrolled ? "is-scrolled" : ""}`}>
        <div className="nav-inner">
          <Link href="/" className="brand-wordmark">
            <span>
              MarketingAgents<b>.ai</b>
            </span>
            <small>AI Marketing OS</small>
          </Link>
          <nav className="nav-links nav-links-desktop">
            {NAV_ITEMS.map((item) => {
              const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
              if (item.href === "/agents") {
                return (
                  <div
                    key={item.href}
                    ref={agentsMenuRef}
                    className={`nav-agents-menu ${agentsOpen ? "open" : ""}`}
                    onMouseEnter={() => setAgentsOpen(true)}
                    onMouseLeave={() => setAgentsOpen(false)}
                  >
                    <Link href={item.href as Route} className={`nav-link ${active ? "active" : ""}`}>
                      {item.label}
                    </Link>
                    <button
                      type="button"
                      className="nav-agents-toggle"
                      aria-label="Toggle Agent Studio categories"
                      aria-expanded={agentsOpen}
                      onClick={(e) => {
                        e.preventDefault();
                        setAgentsOpen((v) => !v);
                      }}
                    >
                      ▾
                    </button>
                    <div className="nav-agents-dropdown">
                      <Link href={"/agents" as Route} className="nav-agents-option">All Categories</Link>
                      {AGENT_CATEGORIES.map((category) => (
                        <Link
                          key={category}
                          href={`/agents?category=${encodeURIComponent(category)}` as Route}
                          className="nav-agents-option"
                        >
                          {category}
                        </Link>
                      ))}
                    </div>
                  </div>
                );
              }
              return (
                <Link key={item.href} href={item.href as Route} className={`nav-link ${active ? "active" : ""}`}>
                  {item.label}
                </Link>
              );
            })}
          </nav>
          {mounted && (
            <div className="nav-actions nav-links-desktop">
              <div className={`nav-usage-indicator ${usageStatus.is_blocked ? "blocked" : ""}`}>
                <div className="nav-usage-text">
                  {usageStatus.tier === "pro" ? 
                   `💯 ${usageStatus.runs_remaining} runs remaining` : 
                   `🚀 ${usageStatus.runs_remaining}/${usageStatus.runs_limit} runs remaining`}
                </div>
                <div className="nav-usage-bar">
                  <div 
                    className="nav-usage-fill" 
                    style={{ width: `${Math.min(100, (usageStatus.runs_used / usageStatus.runs_limit) * 100)}%` }}
                  />
                </div>
              </div>
              
              {pro ? (
                <div className={`nav-auth-menu ${userMenuOpen ? "open" : ""}`} ref={userMenuRef}>
                  <button
                    type="button"
                    className="nav-pro-badge"
                    onClick={() => setUserMenuOpen((v) => !v)}
                  >
                    👑 PRO
                  </button>
                  <div className="nav-auth-dropdown">
                    <div className="nav-auth-info">
                      <span>{getCachedProfile()?.name || getCachedProfile()?.email}</span>
                      <small>👑 Pro Member</small>
                    </div>
                    <button className="nav-auth-link" onClick={() => { setShowGetPro(true); setUserMenuOpen(false); }}>
                      Manage Subscription
                    </button>
                    <button className="nav-auth-link nav-logout" onClick={handleLogout}>
                      Log Out
                    </button>
                  </div>
                </div>
              ) : loggedIn ? (
                <>
                  <div className={`nav-auth-menu ${userMenuOpen ? "open" : ""}`} ref={userMenuRef}>
                    <button
                      type="button"
                      className="nav-auth-toggle"
                      onClick={() => setUserMenuOpen((v) => !v)}
                    >
                      {getCachedProfile()?.name?.[0] || getCachedProfile()?.email?.[0] || "U"} ▾
                    </button>
                    <div className="nav-auth-dropdown">
                      <div className="nav-auth-info">
                        <span>{getCachedProfile()?.name || getCachedProfile()?.email}</span>
                        <small>Free member</small>
                      </div>
                      <button className="nav-auth-link nav-logout" onClick={handleLogout}>
                        Log Out
                      </button>
                    </div>
                  </div>
                  <button className="btn btn-pro" onClick={() => setShowGetPro(true)}>
                    ✨ Upgrade to Pro
                  </button>
                </>
              ) : (
                <>
                  <button className="btn btn-pro" onClick={() => setShowGetPro(true)}>
                    ✨ Upgrade to Pro
                  </button>
                  <button className="nav-login-btn" onClick={() => setShowAuth(true)}>
                    Sign Up
                  </button>
                </>
              )}
            </div>
          )}
          <button
            type="button"
            className={`nav-menu-btn ${menuOpen ? "active" : ""}`}
            aria-label="Toggle menu"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((v) => !v)}
          >
            <span />
            <span />
            <span />
          </button>
        </div>
        <div className={`mobile-nav-overlay ${menuOpen ? "open" : ""}`}>
          <nav className="mobile-nav-links">
            {mounted && (
              <div className={`mobile-usage-indicator ${usageStatus.is_blocked ? "blocked" : ""}`}>
                <span>
                  {usageStatus.tier === "pro" ? 
                   `💯 ${usageStatus.runs_remaining} runs remaining` : 
                   `🚀 ${usageStatus.runs_remaining}/${usageStatus.runs_limit} runs remaining`}
                </span>
              </div>
            )}
            {NAV_ITEMS.map((item, idx) => (
              <Link
                key={item.href}
                href={item.href as Route}
                className="mobile-nav-link"
                style={{ transitionDelay: `${60 * idx}ms` }}
              >
                {item.label}
              </Link>
            ))}
            
            {mounted && (
              <>
                {pro ? (
                  <>
                    <div className="mobile-pro-badge">👑 Pro Member</div>
                    <button className="btn btn-subtle" onClick={() => { setShowGetPro(true); setMenuOpen(false); }}>
                      Manage Subscription
                    </button>
                    <button className="btn btn-subtle" onClick={handleLogout}>Log Out</button>
                  </>
                ) : loggedIn ? (
                  <>
                    <div className="mobile-user-info">
                      <span>{getCachedProfile()?.name || getCachedProfile()?.email}</span>
                      <small>Free member</small>
                    </div>
                    <button className="btn btn-pro" onClick={() => { setShowGetPro(true); setMenuOpen(false); }}>
                      ✨ Upgrade to Pro
                    </button>
                    <button className="btn btn-subtle" onClick={handleLogout}>Log Out</button>
                  </>
                ) : (
                  <>
                    <button className="btn btn-pro" onClick={() => { setShowGetPro(true); setMenuOpen(false); }}>
                      ✨ Upgrade to Pro
                    </button>
                    <button className="btn" onClick={() => { setShowAuth(true); setMenuOpen(false); }}>Sign Up</button>
                  </>
                )}
              </>
            )}
          </nav>
        </div>
      </header>

      <GetProOverlay isOpen={showGetPro} onClose={() => setShowGetPro(false)} />
      <AuthModal isOpen={showAuth} onClose={() => { setShowAuth(false); handleLoginSuccess(); }} />
    </>
  );
}
