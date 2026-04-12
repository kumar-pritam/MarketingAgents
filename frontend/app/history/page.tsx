"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { apiGet } from "../../lib/api";
import { getActiveWorkspaceId } from "../../lib/workspace";

type WorkspaceSummary = {
  workspace_id: string;
  workspace_name: string;
  brand_name: string;
};

function HistoryContent() {
  const searchParams = useSearchParams();
  const agentFilter = searchParams.get("agent");
  const [workspaceId, setWorkspaceId] = useState(getActiveWorkspaceId());
  const [workspaces, setWorkspaces] = useState<WorkspaceSummary[]>([]);
  const [rows, setRows] = useState<any[]>([]);

  useEffect(() => {
    apiGet<WorkspaceSummary[]>("/workspaces")
      .then(setWorkspaces)
      .catch(() => setWorkspaces([]));
  }, []);

  useEffect(() => {
    if (workspaceId) {
      load();
    }
  }, [workspaceId]);

  async function load() {
    const data = await apiGet<any[]>(`/agents/history/${workspaceId}`);
    setRows(data);
  }

  const filteredRows = agentFilter 
    ? rows.filter((row) => row.agent_id === agentFilter)
    : rows;

  const statusCounts = filteredRows.reduce<Record<string, number>>((acc, row) => {
    const key = row.status?.toLowerCase() || "unknown";
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="history-page">
      <section className="hero-strip hero-premium history-hero">
        <div>
          <p className="hero-eyebrow">History</p>
          <h1>Agent run archive</h1>
          <p className="hero-subtext">
            Track every agent execution, compare outputs, and reconnect winning strategies to your current
            Brand Workspace.
          </p>
        </div>
        <div className="hero-stats">
          <div>
            <strong>{filteredRows.length}</strong>
            <span>runs loaded</span>
          </div>
          <div>
            <strong>{filteredRows.filter((row) => row.status === "COMPLETED").length}</strong>
            <span>successful</span>
          </div>
          <div>
            <strong>{filteredRows.filter((row) => row.status !== "COMPLETED").length}</strong>
            <span>under review</span>
          </div>
        </div>
      </section>

      {agentFilter && (
        <div className="card" style={{ marginBottom: "16px", padding: "12px 16px", background: "#f0f9ff", border: "1px solid #bae6fd" }}>
          <span style={{ fontSize: "14px", color: "#0369a1" }}>
            Filtered by agent: <strong>{agentFilter}</strong>
          </span>
          <a href="/history" style={{ marginLeft: "12px", fontSize: "13px", color: "#4f6ef7" }}>Clear filter</a>
        </div>
      )}

      <div className="card history-filter-card">
        <div className="filter-grid">
          <label>
            Workspace
            <select value={workspaceId} onChange={(e) => setWorkspaceId(e.target.value)}>
              <option value="">All workspaces</option>
              {workspaces.map((ws) => (
                <option key={ws.workspace_id} value={ws.workspace_id}>
                  {ws.workspace_name} ({ws.brand_name})
                </option>
              ))}
            </select>
          </label>
          <label>
            Workspace ID
            <input value={workspaceId} onChange={(e) => setWorkspaceId(e.target.value)} placeholder="Paste workspace ID" />
          </label>
          <div className="history-actions">
            <button className="btn btn-subtle" onClick={() => setRows([])}>
              Clear
            </button>
            <button className="btn" onClick={load}>
              Load history
            </button>
          </div>
        </div>
        <div className="status-pills">
          {Object.entries(statusCounts).map(([status, count]) => (
            <span key={status} className={`status-pill ${status}`}>
              {count} {status.replace(/_/g, " ")}
            </span>
          ))}
          {!rows.length && <span className="status-pill muted">No runs yet</span>}
        </div>
      </div>

      <div className="card history-grid">
        {rows.length === 0 ? (
          <div className="history-empty">
            <svg viewBox="0 0 64 64" aria-hidden="true" className="empty-icon">
              <circle cx="32" cy="32" r="28" fill="none" stroke="currentColor" strokeWidth="2" />
              <path d="M32 20v24M20 32h24" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
            <h3>No runs loaded yet</h3>
            <p>Pick a workspace and tap "Load history" to sync your past executions.</p>
            <a href="/agents" className="btn">Run your first agent</a>
          </div>
        ) : (
          filteredRows.map((row) => (
            <article className="history-card" key={row.run_id}>
              <div className="history-card-header">
                <span className="mono">Run {row.run_id}</span>
                <span className="history-card-meta">
                  {row.agent_id} · {row.workspace_name || "Workspace"}
                </span>
              </div>
              <p className="history-card-summary">{row.summary || "AI execution results stored for future reference."}</p>
              <div className="history-card-footer">
                <span className={`status-pill ${row.status?.toLowerCase()}`}>{row.status}</span>
                <button className="btn btn-ghost-sm">View details</button>
              </div>
            </article>
          ))
        )}
      </div>
    </div>
  );
}

export default function HistoryPage() {
  return (
    <Suspense fallback={<div className="history-page"><p>Loading...</p></div>}>
      <HistoryContent />
    </Suspense>
  );
}