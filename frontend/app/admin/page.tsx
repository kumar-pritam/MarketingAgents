"use client";

import { useEffect, useState } from "react";
import {
  adminLogin,
  adminLogout,
  verifyAdmin,
  getConfig,
  updateConfig,
  getUsageStats,
  getUsers,
  getPayments,
  getPendingPayments,
  approvePayment,
  rejectPayment,
  ConfigItem,
  UsageStats,
  UserDetail,
  PaymentDetail,
  PendingPayment,
} from "../../lib/adminApi";
import Link from "next/link";
import type { Route } from "next";

type Tab = "config" | "usage" | "users" | "payments";

export default function AdminPage() {
  const [authenticated, setAuthenticated] = useState(false);
  const [checking, setChecking] = useState(true);
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState("");
  const [activeTab, setActiveTab] = useState<Tab>("config");
  const [loading, setLoading] = useState(false);

  const [config, setConfig] = useState<ConfigItem[]>([]);
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");

  const [usageStats, setUsageStats] = useState<UsageStats | null>(null);
  const [users, setUsers] = useState<UserDetail[]>([]);
  const [payments, setPayments] = useState<PaymentDetail[]>([]);
  const [pendingPayments, setPendingPayments] = useState<PendingPayment[]>([]);
  const [expandedPayment, setExpandedPayment] = useState<string | null>(null);

  useEffect(() => {
    checkAuth();
  }, []);

  async function checkAuth() {
    try {
      const result = await verifyAdmin();
      setAuthenticated(result.authenticated);
      if (result.authenticated) {
        loadData();
      }
    } catch {
      setAuthenticated(false);
    }
    setChecking(false);
  }

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoginError("");
    setLoading(true);

    try {
      const result = await adminLogin(password);
      if (result.success) {
        setAuthenticated(true);
        loadData();
      } else {
        setLoginError(result.message);
      }
    } catch {
      setLoginError("Login failed");
    }
    setLoading(false);
  }

  async function handleLogout() {
    await adminLogout();
    setAuthenticated(false);
    setConfig([]);
    setUsageStats(null);
    setUsers([]);
    setPayments([]);
  }

  async function loadData() {
    try {
      const [configData, usageData, usersData, paymentsData, pendingData] = await Promise.all([
        getConfig(),
        getUsageStats(),
        getUsers(),
        getPayments(),
        getPendingPayments(),
      ]);
      setConfig(configData);
      setUsageStats(usageData);
      setUsers(usersData);
      setPayments(paymentsData);
      setPendingPayments(pendingData);
    } catch (err) {
      console.error("Failed to load data:", err);
    }
  }

  async function handleSaveConfig(key: string) {
    try {
      await updateConfig(key, editValue);
      setEditingKey(null);
      const newConfig = await getConfig();
      setConfig(newConfig);
    } catch (err) {
      console.error("Failed to update config:", err);
    }
  }

  async function handleApprovePayment(paymentId: string, amount: number, billingCycle: string) {
    try {
      await approvePayment(paymentId, amount, billingCycle);
      await loadData();
    } catch (err) {
      console.error("Failed to approve payment:", err);
    }
  }

  async function handleRejectPayment(paymentId: string) {
    try {
      await rejectPayment(paymentId);
      await loadData();
    } catch (err) {
      console.error("Failed to reject payment:", err);
    }
  }

  if (checking) {
    return (
      <div className="admin-loading">
        <div className="admin-spinner" />
        <p>Loading...</p>
      </div>
    );
  }

  if (!authenticated) {
    return (
      <div className="admin-login-page">
        <div className="admin-login-card">
          <h1>🔐 Admin Portal</h1>
          <p>Enter admin password to continue</p>
          <form onSubmit={handleLogin}>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              className="admin-password-input"
              autoFocus
            />
            {loginError && <p className="admin-error">{loginError}</p>}
            <button type="submit" className="admin-login-btn" disabled={loading}>
              {loading ? "Logging in..." : "Login"}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-page">
      <header className="admin-header">
        <div className="admin-header-content">
          <h1>⚙️ Admin Portal</h1>
          <nav className="admin-nav">
            <Link href="/" className="admin-back-link">← Back to App</Link>
            <button onClick={handleLogout} className="admin-logout-btn">Logout</button>
          </nav>
        </div>
      </header>

      <div className="admin-tabs">
        <button
          className={`admin-tab ${activeTab === "config" ? "active" : ""}`}
          onClick={() => setActiveTab("config")}
        >
          ⚙️ Configuration
        </button>
        <button
          className={`admin-tab ${activeTab === "usage" ? "active" : ""}`}
          onClick={() => setActiveTab("usage")}
        >
          📊 Usage Dashboard
        </button>
        <button
          className={`admin-tab ${activeTab === "users" ? "active" : ""}`}
          onClick={() => setActiveTab("users")}
        >
          👥 Users ({users.length})
        </button>
        <button
          className={`admin-tab ${activeTab === "payments" ? "active" : ""}`}
          onClick={() => setActiveTab("payments")}
        >
          💳 Payments ({payments.length})
        </button>
      </div>

      <main className="admin-content">
        {activeTab === "config" && (
          <section className="admin-section">
            <h2>Configuration Settings</h2>
            <p className="admin-section-desc">Manage API keys, pricing, and platform settings</p>

            <div className="config-grid">
              {config.map((item) => (
                <div key={item.key} className="config-item">
                  <div className="config-item-header">
                    <label>{item.key}</label>
                    {editingKey === item.key ? (
                      <div className="config-edit-actions">
                        <button
                          className="config-save-btn"
                          onClick={() => handleSaveConfig(item.key)}
                        >
                          Save
                        </button>
                        <button
                          className="config-cancel-btn"
                          onClick={() => setEditingKey(null)}
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <button
                        className="config-edit-btn"
                        onClick={() => {
                          setEditingKey(item.key);
                          setEditValue(String(item.value));
                        }}
                      >
                        Edit
                      </button>
                    )}
                  </div>
                  <p className="config-desc">{item.description}</p>
                  {editingKey === item.key ? (
                    <input
                      type={item.key.includes("key") || item.key.includes("secret") ? "password" : "text"}
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      className="config-input"
                    />
                  ) : (
                    <div className="config-value">
                      {typeof item.value === "boolean" ? (
                        <span className={`config-bool ${item.value ? "true" : "false"}`}>
                          {item.value ? "✓ Enabled" : "✗ Disabled"}
                        </span>
                      ) : item.key.includes("key") || item.key.includes("secret") ? (
                        <span className="config-sensitive">
                          {item.value ? "••••••••" : "Not set"}
                        </span>
                      ) : (
                        <span>{String(item.value)}</span>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        {activeTab === "usage" && usageStats && (
          <section className="admin-section">
            <h2>Usage Dashboard</h2>
            <p className="admin-section-desc">Platform usage metrics and trends</p>

            <div className="stats-grid">
              <div className="stat-card">
                <span className="stat-icon">🚀</span>
                <div className="stat-content">
                  <span className="stat-value">{usageStats.total_runs}</span>
                  <span className="stat-label">Total Runs</span>
                </div>
              </div>
              <div className="stat-card">
                <span className="stat-icon">👤</span>
                <div className="stat-content">
                  <span className="stat-value">
                    {usageStats.anonymous_users + usageStats.free_users + usageStats.pro_users}
                  </span>
                  <span className="stat-label">Total Users</span>
                </div>
              </div>
              <div className="stat-card">
                <span className="stat-icon">👑</span>
                <div className="stat-content">
                  <span className="stat-value">{usageStats.pro_users}</span>
                  <span className="stat-label">Pro Users</span>
                </div>
              </div>
              <div className="stat-card">
                <span className="stat-icon">💰</span>
                <div className="stat-content">
                  <span className="stat-value">₹{usageStats.revenue_estimate.toLocaleString()}</span>
                  <span className="stat-label">Est. Revenue</span>
                </div>
              </div>
            </div>

            <div className="usage-breakdown">
              <h3>User Breakdown</h3>
              <div className="breakdown-bars">
                <div className="breakdown-item">
                  <span>Anonymous</span>
                  <div className="breakdown-bar">
                    <div
                      className="breakdown-fill anonymous"
                      style={{
                        width: `${(usageStats.anonymous_users / Math.max(1, usageStats.anonymous_users + usageStats.free_users + usageStats.pro_users)) * 100}%`,
                      }}
                    />
                  </div>
                  <span>{usageStats.anonymous_users}</span>
                </div>
                <div className="breakdown-item">
                  <span>Free</span>
                  <div className="breakdown-bar">
                    <div
                      className="breakdown-fill free"
                      style={{
                        width: `${(usageStats.free_users / Math.max(1, usageStats.anonymous_users + usageStats.free_users + usageStats.pro_users)) * 100}%`,
                      }}
                    />
                  </div>
                  <span>{usageStats.free_users}</span>
                </div>
                <div className="breakdown-item">
                  <span>Pro</span>
                  <div className="breakdown-bar">
                    <div
                      className="breakdown-fill pro"
                      style={{
                        width: `${(usageStats.pro_users / Math.max(1, usageStats.anonymous_users + usageStats.free_users + usageStats.pro_users)) * 100}%`,
                      }}
                    />
                  </div>
                  <span>{usageStats.pro_users}</span>
                </div>
              </div>
            </div>

            {usageStats.top_agents.length > 0 && (
              <div className="top-agents">
                <h3>Top Agents</h3>
                <table className="admin-table">
                  <thead>
                    <tr>
                      <th>Agent</th>
                      <th>Runs</th>
                    </tr>
                  </thead>
                  <tbody>
                    {usageStats.top_agents.map((agent) => (
                      <tr key={agent.agent_id}>
                        <td>{agent.agent_id}</td>
                        <td>{agent.runs}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {usageStats.daily_trend.length > 0 && (
              <div className="daily-trend">
                <h3>Daily Trend (Last 30 Days)</h3>
                <div className="trend-chart">
                  {usageStats.daily_trend.map((day, i) => (
                    <div
                      key={day.date}
                      className="trend-bar"
                      style={{ height: `${Math.max(5, (day.runs / Math.max(...usageStats.daily_trend.map((d) => d.runs))) * 100)}%` }}
                      title={`${day.date}: ${day.runs} runs`}
                    />
                  ))}
                </div>
                <div className="trend-labels">
                  <span>{usageStats.daily_trend[0]?.date}</span>
                  <span>{usageStats.daily_trend[usageStats.daily_trend.length - 1]?.date}</span>
                </div>
              </div>
            )}
          </section>
        )}

        {activeTab === "users" && (
          <section className="admin-section">
            <h2>User Details</h2>
            <p className="admin-section-desc">{users.length} registered users</p>

            <table className="admin-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Tier</th>
                  <th>Runs Used</th>
                  <th>Subscribed</th>
                  <th>Expires</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user, i) => (
                  <tr key={i}>
                    <td>{user.name || "-"}</td>
                    <td>{user.email}</td>
                    <td>
                      <span className={`tier-badge ${user.tier}`}>{user.tier}</span>
                    </td>
                    <td>{user.runs_used}</td>
                    <td>{user.subscribed_at ? new Date(user.subscribed_at).toLocaleDateString() : "-"}</td>
                    <td>{user.subscription_expires ? new Date(user.subscription_expires).toLocaleDateString() : "-"}</td>
                  </tr>
                ))}
                {users.length === 0 && (
                  <tr>
                    <td colSpan={6} className="empty-state">No users found</td>
                  </tr>
                )}
              </tbody>
            </table>
          </section>
        )}

        {activeTab === "payments" && (
          <section className="admin-section">
            <h2>Payment Management</h2>
            
            {pendingPayments.length > 0 && (
              <>
                <h3>Pending Payments ({pendingPayments.length})</h3>
                <p className="admin-section-desc">Review and approve or reject payments</p>
                
                <div className="pending-payments">
                  {pendingPayments.map((payment) => (
                    <div key={payment.id} className="pending-payment-card">
                      <div className="pending-payment-header">
                        <div className="pending-payment-info">
                          <strong>{payment.user_name || "Unknown"}</strong>
                          <span>{payment.user_email}</span>
                          <span className="pending-payment-meta">
                            {payment.billing_cycle} • ₹{payment.amount} • {new Date(payment.submitted_at).toLocaleString()}
                          </span>
                        </div>
                        <div className="pending-payment-actions">
                          <button 
                            className="admin-btn-approve"
                            onClick={() => handleApprovePayment(payment.id, payment.amount, payment.billing_cycle)}
                          >
                            ✓ Approve
                          </button>
                          <button 
                            className="admin-btn-reject"
                            onClick={() => handleRejectPayment(payment.id)}
                          >
                            ✗ Reject
                          </button>
                        </div>
                      </div>
                      <div className="pending-payment-screenshot">
                        <button 
                          className="screenshot-toggle"
                          onClick={() => setExpandedPayment(expandedPayment === payment.id ? null : payment.id)}
                        >
                          {expandedPayment === payment.id ? "Hide" : "Show"} Screenshot
                        </button>
                        {expandedPayment === payment.id && (
                          <img 
                            src={`http://localhost:8000/api/v1/admin/payments/${payment.id}/screenshot`}
                            alt="Payment screenshot"
                            className="payment-screenshot-img"
                          />
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
            
            {pendingPayments.length === 0 && (
              <p className="admin-section-desc">No pending payments</p>
            )}
            
            <h3 style={{marginTop: "2rem"}}>Completed Payments</h3>
            <p className="admin-section-desc">{payments.length} recorded payments</p>

            <table className="admin-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Amount</th>
                  <th>Cycle</th>
                  <th>Method</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {payments.map((payment, i) => (
                  <tr key={i}>
                    <td>{payment.date ? new Date(payment.date).toLocaleDateString() : "-"}</td>
                    <td>{payment.user_name || "-"}</td>
                    <td>{payment.user_email}</td>
                    <td>₹{payment.amount}</td>
                    <td>{payment.billing_cycle}</td>
                    <td>{payment.payment_method}</td>
                    <td>
                      <span className={`status-badge ${payment.status}`}>{payment.status}</span>
                    </td>
                  </tr>
                ))}
                {payments.length === 0 && (
                  <tr>
                    <td colSpan={7} className="empty-state">No completed payments</td>
                  </tr>
                )}
              </tbody>
            </table>
          </section>
        )}
      </main>
    </div>
  );
}
