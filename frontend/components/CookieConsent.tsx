"use client";

import { useState, useEffect } from "react";
import { hasAnalyticsConsent, setAnalyticsConsent } from "../lib/analytics";

export function CookieConsent() {
  const [showBanner, setShowBanner] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const consent = hasAnalyticsConsent();
    if (consent === undefined) {
      setShowBanner(true);
    }
  }, []);

  const handleAccept = () => {
    setAnalyticsConsent(true);
    setShowBanner(false);
  };

  const handleDecline = () => {
    setAnalyticsConsent(false);
    setShowBanner(false);
  };

  if (!mounted || !showBanner) return null;

  return (
    <div className="cookie-consent">
      <div className="cookie-consent-content">
        <div className="cookie-consent-text">
          <h3>🍪 We use cookies</h3>
          <p>
            We use cookies to improve your experience and analyze site traffic. 
            By clicking &quot;Accept&quot;, you consent to our use of cookies.
          </p>
        </div>
        <div className="cookie-consent-actions">
          <button className="cookie-btn cookie-decline" onClick={handleDecline}>
            Decline
          </button>
          <button className="cookie-btn cookie-accept" onClick={handleAccept}>
            Accept
          </button>
        </div>
      </div>
      <style jsx>{`
        .cookie-consent {
          position: fixed;
          bottom: 0;
          left: 0;
          right: 0;
          background: white;
          box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
          z-index: 9998;
          padding: 16px 24px;
        }
        
        .cookie-consent-content {
          max-width: 1200px;
          margin: 0 auto;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 24px;
          flex-wrap: wrap;
        }
        
        .cookie-consent-text h3 {
          margin: 0 0 4px;
          font-size: 16px;
          color: #1f2937;
        }
        
        .cookie-consent-text p {
          margin: 0;
          font-size: 13px;
          color: #6b7280;
          max-width: 600px;
        }
        
        .cookie-consent-actions {
          display: flex;
          gap: 12px;
        }
        
        .cookie-btn {
          padding: 10px 20px;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          border: none;
          transition: background 0.2s;
        }
        
        .cookie-decline {
          background: #f3f4f6;
          color: #374151;
        }
        
        .cookie-decline:hover {
          background: #e5e7eb;
        }
        
        .cookie-accept {
          background: #4f6ef7;
          color: white;
        }
        
        .cookie-accept:hover {
          background: #3d5ae5;
        }
        
        @media (max-width: 768px) {
          .cookie-consent-content {
            flex-direction: column;
            text-align: center;
          }
          
          .cookie-consent-actions {
            width: 100%;
            justify-content: center;
          }
        }
      `}</style>
    </div>
  );
}
