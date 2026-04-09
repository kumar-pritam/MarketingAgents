"use client";

import { Component, ReactNode, ErrorInfo } from "react";

type Props = {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
};

type State = {
  hasError: boolean;
  error: Error | null;
};

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
    this.props.onError?.(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <div className="error-boundary">
          <div className="error-boundary-content">
            <div className="error-icon">⚠</div>
            <h2>Something went wrong</h2>
            <p>We apologize for the inconvenience. Please try again or refresh the page.</p>
            <button onClick={() => window.location.reload()} className="error-retry-btn">
              Refresh Page
            </button>
          </div>
          <style jsx>{`
            .error-boundary {
              display: flex;
              align-items: center;
              justify-content: center;
              min-height: 400px;
              padding: 40px;
            }
            
            .error-boundary-content {
              text-align: center;
              max-width: 400px;
            }
            
            .error-icon {
              font-size: 48px;
              margin-bottom: 16px;
            }
            
            h2 {
              margin: 0 0 12px;
              font-size: 24px;
              color: #1f2937;
            }
            
            p {
              margin: 0 0 24px;
              color: #6b7280;
              font-size: 14px;
            }
            
            .error-retry-btn {
              padding: 12px 24px;
              background: #4f6ef7;
              color: white;
              border: none;
              border-radius: 8px;
              font-size: 14px;
              font-weight: 500;
              cursor: pointer;
              transition: background 0.2s;
            }
            
            .error-retry-btn:hover {
              background: #3d5ae5;
            }
          `}</style>
        </div>
      );
    }

    return this.props.children;
  }
}

export function NetworkErrorFallback() {
  return (
    <div className="network-error">
      <div className="network-error-content">
        <div className="network-icon">📡</div>
        <h2>No Internet Connection</h2>
        <p>Please check your connection and try again.</p>
        <button onClick={() => window.location.reload()} className="network-retry-btn">
          Try Again
        </button>
      </div>
      <style jsx>{`
        .network-error {
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: 400px;
          padding: 40px;
        }
        
        .network-error-content {
          text-align: center;
          max-width: 400px;
        }
        
        .network-icon {
          font-size: 48px;
          margin-bottom: 16px;
        }
        
        h2 {
          margin: 0 0 12px;
          font-size: 24px;
          color: #1f2937;
        }
        
        p {
          margin: 0 0 24px;
          color: #6b7280;
          font-size: 14px;
        }
        
        .network-retry-btn {
          padding: 12px 24px;
          background: #4f6ef7;
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: background 0.2s;
        }
        
        .network-retry-btn:hover {
          background: #3d5ae5;
        }
      `}</style>
    </div>
  );
}
