declare global {
  interface Window {
    gtag?: (...args: unknown[]) => void;
    dataLayer?: unknown[];
  }
}

const GA_ID = process.env.NEXT_PUBLIC_GA_ID;
const CONSENT_KEY = "marketing_agents_analytics_consent";

export function hasAnalyticsConsent(): boolean {
  if (typeof window === "undefined") return false;
  return localStorage.getItem(CONSENT_KEY) === "true";
}

export function setAnalyticsConsent(consent: boolean): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(CONSENT_KEY, consent ? "true" : "false");
  if (consent && GA_ID) {
    initGA();
  }
}

export function initGA(): void {
  if (!GA_ID || !hasAnalyticsConsent()) return;
  if (typeof window === "undefined") return;
  
  window.dataLayer = window.dataLayer || [];
  
  window.gtag = function gtag(...args: unknown[]) {
    window.dataLayer!.push(args);
  };
  
  window.gtag("js", new Date());
  window.gtag("config", GA_ID, {
    send_page_view: true,
  });
}

export function trackPageView(path: string, title?: string): void {
  if (!hasAnalyticsConsent() || !window.gtag) return;
  
  window.gtag("event", "page_view", {
    page_path: path,
    page_title: title || document.title,
  });
}

export function trackSignUp(method: string = "email"): void {
  if (!hasAnalyticsConsent() || !window.gtag) return;
  
  window.gtag("event", "sign_up", {
    method,
  });
}

export function trackLogin(method: string = "email"): void {
  if (!hasAnalyticsConsent() || !window.gtag) return;
  
  window.gtag("event", "login", {
    method,
  });
}

export function trackPaymentSubmit(amount: number, billingCycle: string): void {
  if (!hasAnalyticsConsent() || !window.gtag) return;
  
  window.gtag("event", "payment_submit", {
    currency: "INR",
    value: amount,
    billing_cycle: billingCycle,
  });
}

export function trackPaymentApproved(amount: number, billingCycle: string): void {
  if (!hasAnalyticsConsent() || !window.gtag) return;
  
  window.gtag("event", "purchase", {
    currency: "INR",
    value: amount,
    billing_cycle: billingCycle,
  });
}

export function trackUpgradeClick(): void {
  if (!hasAnalyticsConsent() || !window.gtag) return;
  
  window.gtag("event", "upgrade_click", {
    event_category: "engagement",
  });
}

export function trackAgentRun(agentId: string, agentName: string): void {
  if (!hasAnalyticsConsent() || !window.gtag) return;
  
  window.gtag("event", "agent_run", {
    event_category: "engagement",
    event_label: agentId,
    agent_name: agentName,
  });
}

export function trackGetProOpen(): void {
  if (!hasAnalyticsConsent() || !window.gtag) return;
  
  window.gtag("event", "get_pro_open", {
    event_category: "engagement",
  });
}
