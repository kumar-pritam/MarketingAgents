import { isLoggedInSync, isPro, getCachedProfile } from "./auth";
import { trackAgentRun as trackAgentRunGA } from "./analytics";

const ANONYMOUS_LIMIT = 5;
const FREE_USER_LIMIT = 25;
const PRO_LIMIT = 100;
const STORAGE_KEY_ANONYMOUS = "marketing_agents_anonymous_runs";
const STORAGE_KEY_USER_RUNS = "marketing_agents_user_runs";
const STORAGE_KEY_PRO_RUNS = "marketing_agents_pro_runs";
const STORAGE_KEY_PRO_MONTH = "marketing_agents_pro_month";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function trackRunToBackend(agentId: string) {
  try {
    const profile = getCachedProfile();
    const userId = profile?.email || "anonymous";
    await fetch(`${API_BASE}/admin/track-run?agent_id=${encodeURIComponent(agentId)}&user_id=${encodeURIComponent(userId)}`, {
      method: "POST",
    });
  } catch (err) {
    console.error("Failed to track run:", err);
  }
}

export type UserTierDisplay = "anonymous" | "free" | "pro";
export type UserStatus = {
  tier: UserTierDisplay;
  runs_used: number;
  runs_limit: number;
  runs_remaining: number | "Unlimited";
  is_blocked: boolean;
  block_reason: "signup" | "upgrade" | null;
};

export function getAnonymousRuns(): number {
  if (typeof window === "undefined") return 0;
  const stored = localStorage.getItem(STORAGE_KEY_ANONYMOUS);
  return stored ? parseInt(stored, 10) : 0;
}

export function getUserRuns(): number {
  if (typeof window === "undefined") return 0;
  const stored = localStorage.getItem(STORAGE_KEY_USER_RUNS);
  return stored ? parseInt(stored, 10) : 0;
}

export function getProRuns(): number {
  if (typeof window === "undefined") return 0;
  const stored = localStorage.getItem(STORAGE_KEY_PRO_RUNS);
  return stored ? parseInt(stored, 10) : 0;
}

function checkAndResetProRuns(): void {
  if (typeof window === "undefined") return;
  const profile = getCachedProfile();
  if (!profile || profile.tier !== "pro") return;
  
  const now = new Date();
  const currentMonth = `${now.getFullYear()}-${now.getMonth()}`;
  const storedMonth = localStorage.getItem(STORAGE_KEY_PRO_MONTH);
  
  if (storedMonth !== currentMonth) {
    localStorage.setItem(STORAGE_KEY_PRO_RUNS, "0");
    localStorage.setItem(STORAGE_KEY_PRO_MONTH, currentMonth);
  }
}

export function getRunsUsed(): number {
  if (isPro()) {
    checkAndResetProRuns();
    return getProRuns();
  }
  if (isLoggedInSync()) {
    return getUserRuns();
  }
  return getAnonymousRuns();
}

export function incrementRuns(agentId: string = "unknown"): void {
  if (typeof window === "undefined") return;
  
  if (isPro()) {
    checkAndResetProRuns();
    const current = getProRuns();
    localStorage.setItem(STORAGE_KEY_PRO_RUNS, String(current + 1));
  } else if (isLoggedInSync()) {
    const current = getUserRuns();
    localStorage.setItem(STORAGE_KEY_USER_RUNS, String(current + 1));
  } else {
    const current = getAnonymousRuns();
    localStorage.setItem(STORAGE_KEY_ANONYMOUS, String(current + 1));
  }
  
  // Track run to backend for admin portal
  trackRunToBackend(agentId);
  
  // Track to GA4
  const profile = getCachedProfile();
  trackAgentRunGA(agentId, agentId);
}

export { trackAgentRunGA as trackAgentRun };

export function migrateAnonymousToUser(): void {
  if (typeof window === "undefined") return;
  const anonymousRuns = getAnonymousRuns();
  if (anonymousRuns > 0) {
    localStorage.setItem(STORAGE_KEY_USER_RUNS, String(anonymousRuns));
    localStorage.removeItem(STORAGE_KEY_ANONYMOUS);
  }
}

export function getUserStatus(): UserStatus {
  const isUserLoggedIn = isLoggedInSync();
  const isUserPro = isPro();
  
  let tier: UserTierDisplay;
  let runs_limit: number;
  let is_blocked = false;
  let block_reason: "signup" | "upgrade" | null = null;
  
  if (isUserPro) {
    tier = "pro";
    checkAndResetProRuns();
    runs_limit = PRO_LIMIT;
    // Pro users never blocked - just show remaining runs
  } else if (isUserLoggedIn) {
    tier = "free";
    runs_limit = FREE_USER_LIMIT;
    const runs_used = getUserRuns();
    if (runs_used >= FREE_USER_LIMIT) {
      is_blocked = true;
      block_reason = "upgrade";
    }
  } else {
    tier = "anonymous";
    runs_limit = ANONYMOUS_LIMIT;
    const runs_used = getAnonymousRuns();
    if (runs_used >= ANONYMOUS_LIMIT) {
      is_blocked = true;
      block_reason = "signup";
    }
  }
  
  const runs_used = getRunsUsed();
  return {
    tier,
    runs_used,
    runs_limit,
    runs_remaining: tier === "pro" ? Math.max(0, PRO_LIMIT - runs_used) : Math.max(0, runs_limit - runs_used),
    is_blocked,
    block_reason,
  };
}

export function canRun(): { allowed: boolean; reason?: string } {
  const status = getUserStatus();
  
  if (status.is_blocked) {
    if (status.block_reason === "signup") {
      return { allowed: false, reason: "sign-up" };
    }
    if (status.block_reason === "upgrade") {
      return { allowed: false, reason: "upgrade" };
    }
  }
  
  return { allowed: true };
}

export function getUsageMessage(): string {
  const status = getUserStatus();
  
  if (status.tier === "pro") {
    const remaining = typeof status.runs_remaining === "number" ? status.runs_remaining : 0;
    return `💯 ${remaining} runs remaining`;
  }
  if (status.tier === "anonymous") {
    const remaining = typeof status.runs_remaining === "number" ? status.runs_remaining : 0;
    if (remaining <= 0) {
      return "You've used all 5 free runs";
    }
    return `You have ${remaining} of ${status.runs_limit} free runs left`;
  }
  
  const remaining = typeof status.runs_remaining === "number" ? status.runs_remaining : 0;
  if (remaining <= 0) {
    return "You've used all 25 free runs";
  }
  return `You have ${remaining} of ${status.runs_limit} runs left`;
}

export function resetUsage(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(STORAGE_KEY_ANONYMOUS);
  localStorage.removeItem(STORAGE_KEY_USER_RUNS);
  localStorage.removeItem(STORAGE_KEY_PRO_RUNS);
  localStorage.removeItem(STORAGE_KEY_PRO_MONTH);
}
