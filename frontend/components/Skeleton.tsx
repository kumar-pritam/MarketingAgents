"use client";

type SkeletonProps = {
  width?: string;
  height?: string;
  borderRadius?: string;
  className?: string;
};

export function Skeleton({ width = "100%", height = "20px", borderRadius = "6px", className = "" }: SkeletonProps) {
  return (
    <div
      className={`skeleton ${className}`}
      style={{ width, height, borderRadius }}
    />
  );
}

export function SkeletonText({ lines = 3, lastLineWidth = "60%" }: { lines?: number; lastLineWidth?: string }) {
  return (
    <div className="skeleton-text">
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          height="14px"
          width={i === lines - 1 ? lastLineWidth : "100%"}
        />
      ))}
    </div>
  );
}

export function SkeletonCard() {
  return (
    <div className="skeleton-card">
      <Skeleton height="160px" borderRadius="8px" />
      <div className="skeleton-card-content">
        <Skeleton height="20px" width="70%" />
        <Skeleton height="14px" />
        <Skeleton height="14px" width="80%" />
      </div>
      <style jsx>{`
        .skeleton-card {
          background: white;
          border-radius: 12px;
          overflow: hidden;
          padding: 16px;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        
        .skeleton-card-content {
          display: flex;
          flex-direction: column;
          gap: 10px;
          margin-top: 12px;
        }
      `}</style>
    </div>
  );
}

export function SkeletonRow({ columns = 4 }: { columns?: number }) {
  const widths = ["15%", "30%", "35%", "20%"];
  return (
    <div className="skeleton-row">
      {Array.from({ length: columns }).map((_, i) => (
        <Skeleton key={i} height="16px" width={widths[i] || "20%"} />
      ))}
    </div>
  );
}

export function SkeletonAgentCard() {
  return (
    <div className="skeleton-agent-card">
      <div className="skeleton-agent-icon">
        <Skeleton width="48px" height="48px" borderRadius="12px" />
      </div>
      <div className="skeleton-agent-content">
        <Skeleton height="18px" width="70%" />
        <Skeleton height="13px" />
        <Skeleton height="13px" width="85%" />
      </div>
      <div className="skeleton-agent-footer">
        <Skeleton width="80px" height="28px" borderRadius="14px" />
      </div>
      <style jsx>{`
        .skeleton-agent-card {
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 16px;
          background: white;
          border-radius: 12px;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        
        .skeleton-agent-content {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
      `}</style>
    </div>
  );
}

export function SkeletonWorkspaceCard() {
  return (
    <div className="skeleton-workspace-card">
      <div className="skeleton-workspace-header">
        <Skeleton width="40px" height="40px" borderRadius="8px" />
        <div className="skeleton-workspace-info">
          <Skeleton height="18px" width="150px" />
          <Skeleton height="13px" width="200px" />
        </div>
      </div>
      <div className="skeleton-workspace-body">
        <Skeleton height="13px" />
        <Skeleton height="13px" width="90%" />
      </div>
      <div className="skeleton-workspace-footer">
        <Skeleton width="60px" height="24px" borderRadius="12px" />
        <Skeleton width="60px" height="24px" borderRadius="12px" />
      </div>
      <style jsx>{`
        .skeleton-workspace-card {
          background: white;
          border-radius: 12px;
          padding: 20px;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        
        .skeleton-workspace-header {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 16px;
        }
        
        .skeleton-workspace-info {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        
        .skeleton-workspace-body {
          display: flex;
          flex-direction: column;
          gap: 8px;
          margin-bottom: 16px;
        }
        
        .skeleton-workspace-footer {
          display: flex;
          gap: 8px;
        }
      `}</style>
    </div>
  );
}

export function SkeletonPage() {
  return (
    <div className="skeleton-page">
      <div className="skeleton-page-header">
        <Skeleton height="32px" width="200px" />
        <Skeleton height="40px" width="120px" />
      </div>
      <div className="skeleton-page-content">
        {Array.from({ length: 6 }).map((_, i) => (
          <SkeletonAgentCard key={i} />
        ))}
      </div>
      <style jsx>{`
        .skeleton-page {
          padding: 24px;
        }
        
        .skeleton-page-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 24px;
        }
        
        .skeleton-page-content {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
          gap: 16px;
        }
      `}</style>
    </div>
  );
}
