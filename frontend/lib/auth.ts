export type UserTier = "anonymous" | "free" | "pro";

export type UserProfile = {
  id?: number;
  tier: UserTier;
  email?: string;
  name?: string;
  subscribed_at?: string;
  subscription_expires?: string;
  pro_started_at?: string;
  pro_runs_used?: number;
  created_at?: string;
  must_set_password?: boolean;
};

export type RefundEligibility = {
  eligible: boolean;
  refundPercent: number;
  reason: string;
  daysSinceSubscription: number;
  runsUsedSinceSubscription: number;
};

const STORAGE_KEY_USER = "marketing_agents_user_profile";
const STORAGE_KEY_PRO_RUNS_TRACKER = "marketing_agents_pro_runs_tracker";
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function apiCall(endpoint: string, options: RequestInit = {}) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    credentials: "include",
  });
  return response;
}

export async function getUserProfile(): Promise<UserProfile | null> {
  try {
    const response = await apiCall("/auth/me");
    if (response.ok) {
      const user = await response.json();
      localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(user));
      return user;
    }
    return null;
  } catch {
    return null;
  }
}

export function getCachedProfile(): UserProfile | null {
  if (typeof window === "undefined") return null;
  const stored = localStorage.getItem(STORAGE_KEY_USER);
  if (!stored) return null;
  try {
    return JSON.parse(stored) as UserProfile;
  } catch {
    return null;
  }
}

export async function isLoggedIn(): Promise<boolean> {
  try {
    const response = await apiCall("/auth/me");
    return response.ok;
  } catch {
    return false;
  }
}

export function isLoggedInSync(): boolean {
  if (typeof window === "undefined") return false;
  return localStorage.getItem(STORAGE_KEY_USER) !== null;
}

export function getUserTier(): UserTier {
  const profile = getCachedProfile();
  if (!profile) return "anonymous";
  
  if (profile.tier === "pro") {
    if (profile.subscription_expires) {
      const expires = new Date(profile.subscription_expires);
      if (expires < new Date()) {
        return "free";
      }
    }
    return "pro";
  }
  
  return profile.tier || "free";
}

export function isPro(): boolean {
  return getUserTier() === "pro";
}

export async function signUp(name: string, email: string, password: string): Promise<{ success: boolean; user?: UserProfile; error?: string }> {
  try {
    const response = await apiCall("/auth/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, name, password }),
    });
    
    const data = await response.json();
    
    if (response.ok) {
      localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(data.user));
      return { success: true, user: data.user };
    }
    
    return { success: false, error: data.detail || "Signup failed" };
  } catch (err) {
    return { success: false, error: "Network error" };
  }
}

export async function login(email: string, password: string): Promise<{ success: boolean; user?: UserProfile; error?: string; mustSetPassword?: boolean }> {
  try {
    const response = await apiCall("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    
    const data = await response.json();
    
    if (response.ok) {
      localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(data.user));
      return { success: true, user: data.user };
    }
    
    if (response.headers.get("X-Must-Set-Password") === "true") {
      return { success: false, error: data.detail, mustSetPassword: true };
    }
    
    return { success: false, error: data.detail || "Login failed" };
  } catch (err) {
    return { success: false, error: "Network error" };
  }
}

export async function logout(): Promise<void> {
  try {
    await apiCall("/auth/logout", { method: "POST" });
  } catch {
    // ignore
  }
  localStorage.removeItem(STORAGE_KEY_USER);
}

export async function setPassword(password: string): Promise<{ success: boolean; error?: string }> {
  try {
    const response = await apiCall("/auth/set-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
    });
    
    if (response.ok) {
      const profile = getCachedProfile();
      if (profile) {
        profile.must_set_password = false;
        localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(profile));
      }
      return { success: true };
    }
    
    const data = await response.json();
    return { success: false, error: data.detail };
  } catch {
    return { success: false, error: "Network error" };
  }
}

export function updateCachedProfile(updates: Partial<UserProfile>): UserProfile | null {
  const current = getCachedProfile();
  if (!current) return null;
  const updated = { ...current, ...updates };
  localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(updated));
  return updated;
}

export function upgradeToPro(paymentMethod: "upi" | "card", billingCycle: "monthly" | "yearly"): UserProfile | null {
  const profile = getCachedProfile();
  if (!profile) return null;
  
  const now = new Date();
  const expires = new Date(now);
  if (billingCycle === "yearly") {
    expires.setFullYear(expires.getFullYear() + 1);
  } else {
    expires.setMonth(expires.getMonth() + 1);
  }
  
  const updated: UserProfile = {
    ...profile,
    tier: "pro",
    subscribed_at: now.toISOString(),
    subscription_expires: expires.toISOString(),
    pro_started_at: profile.pro_started_at || now.toISOString(),
  };
  
  localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(updated));
  return updated;
}

export function cancelSubscription(): UserProfile | null {
  const profile = getCachedProfile();
  if (!profile) return null;
  
  const updated: UserProfile = {
    ...profile,
    tier: "free",
    subscription_expires: undefined,
  };
  
  localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(updated));
  return updated;
}

export function getSubscriptionStatus(): { isActive: boolean; expiresAt: string | null; daysRemaining: number } {
  const profile = getCachedProfile();
  
  if (!profile || profile.tier !== "pro" || !profile.subscription_expires) {
    return { isActive: false, expiresAt: null, daysRemaining: 0 };
  }
  
  const expires = new Date(profile.subscription_expires);
  const now = new Date();
  const diffTime = expires.getTime() - now.getTime();
  const daysRemaining = Math.max(0, Math.ceil(diffTime / (1000 * 60 * 60 * 24)));
  
  return {
    isActive: daysRemaining > 0,
    expiresAt: profile.subscription_expires,
    daysRemaining,
  };
}

export function getProRunsTracker(): { date: string; runs: number }[] {
  if (typeof window === "undefined") return [];
  const stored = localStorage.getItem(STORAGE_KEY_PRO_RUNS_TRACKER);
  if (!stored) return [];
  try {
    return JSON.parse(stored);
  } catch {
    return [];
  }
}

export function trackProRun(): void {
  if (typeof window === "undefined") return;
  const profile = getCachedProfile();
  if (!profile || profile.tier !== "pro") return;
  
  const today = new Date().toISOString().split("T")[0];
  const tracker = getProRunsTracker();
  const todayIndex = tracker.findIndex((t) => t.date === today);
  
  if (todayIndex >= 0) {
    tracker[todayIndex].runs += 1;
  } else {
    tracker.push({ date: today, runs: 1 });
  }
  
  localStorage.setItem(STORAGE_KEY_PRO_RUNS_TRACKER, JSON.stringify(tracker));
}

export function getTotalProRunsUsed(): number {
  const tracker = getProRunsTracker();
  return tracker.reduce((sum, t) => sum + t.runs, 0);
}

export function getRefundEligibility(): RefundEligibility {
  const profile = getCachedProfile();
  
  if (!profile || profile.tier !== "pro" || !profile.pro_started_at) {
    return {
      eligible: false,
      refundPercent: 0,
      reason: "No active subscription",
      daysSinceSubscription: 0,
      runsUsedSinceSubscription: 0,
    };
  }
  
  const startDate = new Date(profile.pro_started_at);
  const now = new Date();
  const diffTime = now.getTime() - startDate.getTime();
  const daysSinceSubscription = Math.floor(diffTime / (1000 * 60 * 60 * 24));
  const runsUsedSinceSubscription = getTotalProRunsUsed();
  
  if (daysSinceSubscription <= 7 && runsUsedSinceSubscription <= 10) {
    return {
      eligible: true,
      refundPercent: 100,
      reason: "100% refund available",
      daysSinceSubscription,
      runsUsedSinceSubscription,
    };
  }
  
  if (daysSinceSubscription <= 15 && runsUsedSinceSubscription <= 50) {
    return {
      eligible: true,
      refundPercent: 50,
      reason: "50% refund available",
      daysSinceSubscription,
      runsUsedSinceSubscription,
    };
  }
  
  let reason = "Not eligible for refund";
  if (daysSinceSubscription > 15) {
    reason = "Refund period has expired (15 days)";
  } else if (runsUsedSinceSubscription > 50) {
    reason = "Too many runs used for partial refund";
  }
  
  return {
    eligible: false,
    refundPercent: 0,
    reason,
    daysSinceSubscription,
    runsUsedSinceSubscription,
  };
}

export function requestRefund(): { success: boolean; message: string; refundAmount?: number } {
  const profile = getCachedProfile();
  const eligibility = getRefundEligibility();
  const price = 1000;
  
  if (!profile || !eligibility.eligible) {
    return { success: false, message: "You are not eligible for a refund." };
  }
  
  const refundAmount = Math.round(price * (eligibility.refundPercent / 100));
  
  updateCachedProfile({
    tier: "free",
    subscription_expires: undefined,
    pro_started_at: undefined,
  });
  
  localStorage.removeItem(STORAGE_KEY_PRO_RUNS_TRACKER);
  
  return {
    success: true,
    message: `Refund of ₹${refundAmount} has been requested. You will receive the amount within 5-7 business days.`,
    refundAmount,
  };
}
