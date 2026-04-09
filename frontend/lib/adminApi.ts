const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface ConfigItem {
  key: string;
  value: any;
  description: string;
}

export interface UsageStats {
  total_runs: number;
  anonymous_runs: number;
  free_user_runs: number;
  pro_runs: number;
  anonymous_users: number;
  free_users: number;
  pro_users: number;
  daily_trend: { date: string; runs: number }[];
  hourly_trend: { hour: number; runs: number }[];
  top_agents: { agent_id: string; runs: number }[];
  revenue_estimate: number;
}

export interface UserDetail {
  email: string;
  name: string;
  tier: string;
  subscribed_at: string | null;
  subscription_expires: string | null;
  runs_used: number;
  created_at: string | null;
}

export interface PaymentDetail {
  user_email: string;
  user_name: string;
  amount: number;
  billing_cycle: string;
  payment_method: string;
  status: string;
  date: string;
}

export interface PendingPayment {
  id: string;
  user_email: string;
  user_name: string;
  billing_cycle: string;
  amount: number;
  screenshot_path: string;
  status: string;
  submitted_at: string;
}

export async function submitPayment(
  userEmail: string,
  userName: string,
  billingCycle: string,
  amount: number,
  screenshotData: string
): Promise<{ success: boolean; message: string; payment_id?: string }> {
  const res = await fetch(`${API_BASE}/admin/payments/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_email: userEmail,
      user_name: userName,
      billing_cycle: billingCycle,
      amount,
      screenshot_data: screenshotData,
    }),
  });
  return res.json();
}

export async function getPendingPayments(): Promise<PendingPayment[]> {
  const res = await fetch(`${API_BASE}/admin/payments/pending`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Not authenticated");
  return res.json();
}

export async function approvePayment(
  paymentId: string,
  amount?: number,
  billingCycle?: string
): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/admin/payments/${paymentId}/approve`, {
    method: "POST",
    credentials: "include",
  });
  const result = await res.json();
  
  if (result.success && amount && billingCycle && typeof window !== "undefined") {
    try {
      const { trackPaymentApproved } = await import("./analytics");
      trackPaymentApproved(amount, billingCycle);
    } catch (e) {
      console.error("Failed to track payment approval:", e);
    }
  }
  
  return result;
}

export async function rejectPayment(paymentId: string): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/admin/payments/${paymentId}/reject`, {
    method: "POST",
    credentials: "include",
  });
  return res.json();
}

export async function updateUserTier(email: string, tier: string): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/admin/users/tier`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ email, tier }),
  });
  return res.json();
}

export async function adminLogin(password: string): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/admin/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ password }),
  });
  return res.json();
}

export async function adminLogout(): Promise<void> {
  await fetch(`${API_BASE}/admin/logout`, {
    method: "POST",
    credentials: "include",
  });
}

export async function verifyAdmin(): Promise<{ authenticated: boolean }> {
  const res = await fetch(`${API_BASE}/admin/verify`, {
    credentials: "include",
  });
  return res.json();
}

export async function getConfig(): Promise<ConfigItem[]> {
  const res = await fetch(`${API_BASE}/admin/config`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Not authenticated");
  return res.json();
}

export async function updateConfig(key: string, value: any): Promise<void> {
  const res = await fetch(`${API_BASE}/admin/config`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ key, value }),
  });
  if (!res.ok) throw new Error("Failed to update config");
}

export async function getUsageStats(): Promise<UsageStats> {
  const res = await fetch(`${API_BASE}/admin/usage`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Not authenticated");
  return res.json();
}

export async function getUsers(): Promise<UserDetail[]> {
  const res = await fetch(`${API_BASE}/admin/users`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Not authenticated");
  return res.json();
}

export async function getPayments(): Promise<PaymentDetail[]> {
  const res = await fetch(`${API_BASE}/admin/payments`, {
    credentials: "include",
  });
  if (!res.ok) throw new Error("Not authenticated");
  return res.json();
}
