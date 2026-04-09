"use client";

import { useState, useEffect, useRef } from "react";
import { 
  upgradeToPro, 
  cancelSubscription, 
  isLoggedInSync, 
  getCachedProfile, 
  isPro, 
  signUp, 
  login,
  getRefundEligibility, 
  requestRefund,
  setPassword as setPasswordAPI,
} from "../lib/auth";
import { getSubscriptionStatus } from "../lib/auth";
import { showConfirm } from "./ConfirmModal";
import { submitPayment } from "../lib/adminApi";
import { trackSignUp, trackLogin, trackPaymentSubmit } from "../lib/analytics";

type GetProOverlayProps = {
  isOpen: boolean;
  onClose: () => void;
};

type AuthMode = "login" | "signup" | "setpassword";
type PaymentStep = "scan" | "upload" | "success";

export function GetProOverlay({ isOpen, onClose }: GetProOverlayProps) {
  const [authMode, setAuthMode] = useState<AuthMode>("signup");
  const [email, setEmail] = useState("");
  const [password, setPasswordState] = useState("");
  const [name, setName] = useState("");
  const [billingCycle, setBillingCycle] = useState<"monthly" | "yearly">("monthly");
  const [paymentStep, setPaymentStep] = useState<"auth" | PaymentStep>("auth");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [screenshot, setScreenshot] = useState<File | null>(null);
  const [refundMessage, setRefundMessage] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const userLoggedIn = isLoggedInSync();
  const userPro = isPro();
  const profile = getCachedProfile();
  const subscriptionStatus = getSubscriptionStatus();
  const refundEligibility = getRefundEligibility();
  
  const mustSetPassword = profile?.must_set_password;
  
  const price = billingCycle === "monthly" ? "₹1,000" : "₹9,000";
  const priceNote = billingCycle === "monthly" ? "per month" : "per year (save ₹3,000!)";
  
  useEffect(() => {
    if (isOpen) {
      if (mustSetPassword) {
        setAuthMode("setpassword");
      } else if (userLoggedIn && !userPro) {
        setPaymentStep("scan");
        setAuthMode("login");
      } else {
        setPaymentStep("auth");
      }
    }
  }, [isOpen, userLoggedIn, userPro, mustSetPassword]);
  
  if (!isOpen) return null;
  
  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    
    try {
      if (authMode === "signup") {
        if (!name.trim()) {
          setError("Please enter your name");
          setLoading(false);
          return;
        }
        if (!email.includes("@")) {
          setError("Please enter a valid email");
          setLoading(false);
          return;
        }
        if (!password || password.length < 1) {
          setError("Please enter a password");
          setLoading(false);
          return;
        }
        
        const result = await signUp(name, email, password);
        if (result.success) {
          trackSignUp("email");
          setPaymentStep("scan");
        } else {
          setError(result.error || "Signup failed");
        }
      } else if (authMode === "login") {
        if (!email.includes("@")) {
          setError("Please enter a valid email");
          setLoading(false);
          return;
        }
        if (!password) {
          setError("Please enter your password");
          setLoading(false);
          return;
        }
        
        const result = await login(email, password);
        if (result.success) {
          trackLogin("email");
          if (result.mustSetPassword) {
            setAuthMode("setpassword");
            setError("");
          } else {
            setPaymentStep("scan");
          }
        } else {
          setError(result.error || "Login failed");
        }
      } else if (authMode === "setpassword") {
        if (!password || password.length < 1) {
          setError("Please enter a password");
          setLoading(false);
          return;
        }
        
        const result = await setPasswordAPI(password);
        if (result && result.success) {
          setAuthMode("login");
          setPasswordState("");
          setError("");
        } else {
          setError((result as any).error || "Failed to set password");
        }
      }
    } catch (err) {
      setError("Something went wrong. Please try again.");
    }
    setLoading(false);
  };
  
  const handlePayment = async () => {
    setLoading(true);
    setTimeout(() => {
      setPaymentStep("upload");
      setLoading(false);
    }, 1000);
  };
  
  const handleScreenshotUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setScreenshot(file);
    }
  };
  
  const handleSubmitScreenshot = async () => {
    if (!screenshot) {
      setError("Please upload a screenshot of your payment");
      return;
    }
    
    setLoading(true);
    setError("");
    
    try {
      const reader = new FileReader();
      const screenshotData = await new Promise<string>((resolve, reject) => {
        reader.onload = () => resolve(reader.result as string);
        reader.onerror = reject;
        reader.readAsDataURL(screenshot);
      });
      
      const currentProfile = getCachedProfile();
      const amount = billingCycle === "monthly" ? 1000 : 9000;
      
      const result = await submitPayment(
        currentProfile?.email || email,
        currentProfile?.name || name,
        billingCycle,
        amount,
        screenshotData
      );
      
      if (result.success) {
        trackPaymentSubmit(amount, billingCycle);
        setPaymentStep("success");
      } else {
        setError(result.message || "Failed to submit payment");
      }
    } catch (err) {
      setError("Failed to submit payment. Please try again.");
    }
    
    setLoading(false);
  };
  
  const handleRefundRequest = async () => {
    const confirmed = await showConfirm(
      "Request Refund",
      `Are you sure you want to request a ${refundEligibility.refundPercent}% refund?`,
      {
        confirmText: "Request Refund",
        confirmStyle: "danger",
      }
    );
    
    if (confirmed) {
      const result = requestRefund();
      setRefundMessage(result.message);
      if (result.success) {
        setTimeout(() => {
          window.location.reload();
        }, 3000);
      }
    }
  };

  const handleCancelSubscription = async () => {
    const confirmed = await showConfirm(
      "Cancel Subscription",
      "Are you sure you want to cancel your subscription?",
      {
        confirmText: "Cancel Subscription",
        confirmStyle: "danger",
      }
    );
    
    if (confirmed) {
      cancelSubscription();
      window.location.reload();
    }
  };
  
  return (
    <div className="getpro-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="getpro-modal">
        <button className="getpro-close" onClick={onClose}>×</button>
        
        {userPro ? (
          <div className="getpro-pro-user">
            <div className="getpro-pro-badge">👑 PRO</div>
            <h2>You&apos;re a Pro Member! 🎉</h2>
            <p>Thank you for supporting MarketingAgents.ai</p>
            
            {subscriptionStatus.expiresAt && (
              <div className="getpro-subscription-info">
                <p>Your subscription {subscriptionStatus.daysRemaining > 0 ? `renews in ${subscriptionStatus.daysRemaining} days` : "has expired"}</p>
                {subscriptionStatus.expiresAt && (
                  <small>Next billing date: {new Date(subscriptionStatus.expiresAt).toLocaleDateString()}</small>
                )}
              </div>
            )}
            
            <div className="getpro-pro-features">
              <div className="getpro-feature">
                <span>💯</span> 100 runs per month
              </div>
              <div className="getpro-feature">
                <span>🎯</span> Priority support
              </div>
              <div className="getpro-feature">
                <span>🤖</span> All 24 specialist agents
              </div>
            </div>
            
            {refundEligibility.eligible && (
              <div className="getpro-refund-section">
                <div className="getpro-refund-eligible">
                  <span className="refund-badge">{refundEligibility.refundPercent}% Refund Eligible</span>
                  <p>Days since upgrade: {refundEligibility.daysSinceSubscription}</p>
                  <p>Runs used: {refundEligibility.runsUsedSinceSubscription}</p>
                  {refundMessage && <p className="refund-message">{refundMessage}</p>}
                  <button className="getpro-btn-refund" onClick={handleRefundRequest}>
                    Request Refund
                  </button>
                </div>
              </div>
            )}
            
            {!refundEligibility.eligible && subscriptionStatus.isActive && (
              <div className="getpro-refund-info">
                <h4>💰 Refund Policy</h4>
                <ul>
                  <li>100% refund within 7 days &amp; ≤10 runs used</li>
                  <li>50% refund within 15 days &amp; ≤50 runs used</li>
                </ul>
                <small>Your runs: {refundEligibility.runsUsedSinceSubscription} | Days: {refundEligibility.daysSinceSubscription}</small>
              </div>
            )}
            
            <button className="getpro-btn-secondary" onClick={handleCancelSubscription}>
              Cancel Subscription
            </button>
          </div>
        ) : (
          <>
            <div className="getpro-header">
              <h2>{userLoggedIn ? "✨ Upgrade to Pro" : "🚀 Get Started"}</h2>
              <p>{userLoggedIn ? "Get 100 runs per month" : "Create your free account to continue"}</p>
            </div>
            
            {paymentStep === "auth" ? (
              <form className="getpro-auth-form" onSubmit={handleAuth}>
                {authMode === "signup" && (
                  <div className="getpro-field">
                    <label>Your Name</label>
                    <input
                      type="text"
                      placeholder="Priya Sharma"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                    />
                  </div>
                )}
                
                <div className="getpro-field">
                  <label>Email Address</label>
                  <input
                    type="email"
                    placeholder="priya@company.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>
                
                <div className="getpro-field">
                  <label>{authMode === "setpassword" ? "New Password" : "Password"}</label>
                  <input
                    type="password"
                    placeholder="Enter password"
                    value={password}
                    onChange={(e) => setPasswordState(e.target.value)}
                  />
                </div>
                
                {error && <p className="getpro-error">{error}</p>}
                
                <button type="submit" className="getpro-btn-primary" disabled={loading}>
                  {loading ? "Processing..." : authMode === "setpassword" ? "Set Password" : authMode === "signup" ? "Create Account →" : "Continue →"}
                </button>
                
                {authMode === "setpassword" && (
                  <p className="getpro-switch">
                    Already have a password? <button type="button" onClick={() => setAuthMode("login")}>Login</button>
                  </p>
                )}
                {authMode === "setpassword" ? (
                  <p className="getpro-switch">
                    Set a password to secure your account
                  </p>
                ) : userLoggedIn ? (
                  <p className="getpro-switch">
                    New here? <button type="button" onClick={() => setAuthMode("signup")}>Sign up</button>
                  </p>
                ) : (
                  <p className="getpro-switch">
                    Already have an account? <button type="button" onClick={() => setAuthMode("login")}>Log in</button>
                  </p>
                )}
              </form>
            ) : paymentStep === "success" ? (
              <div className="getpro-payment-success">
                <div className="success-icon">🎉</div>
                <h3>Payment Submitted!</h3>
                <p>We will verify and activate your Pro membership within 24 hours.</p>
                <button className="getpro-btn-primary" onClick={() => { onClose(); window.location.reload(); }}>
                  Done
                </button>
              </div>
            ) : (
              <div className="getpro-payment">
                <div className="getpro-payment-grid">
                  <div className="getpro-payment-left">
                    <div className="getpro-qr-section">
                      <h4>📱 Scan to Pay</h4>
                      <div className="getpro-qr-code">
                        <svg viewBox="0 0 100 100" className="qr-svg">
                          <rect x="10" y="10" width="25" height="25" fill="#1a1a2e" />
                          <rect x="15" y="15" width="15" height="15" fill="#fff" />
                          <rect x="18" y="18" width="9" height="9" fill="#1a1a2e" />
                          <rect x="65" y="10" width="25" height="25" fill="#1a1a2e" />
                          <rect x="70" y="15" width="15" height="15" fill="#fff" />
                          <rect x="73" y="18" width="9" height="9" fill="#1a1a2e" />
                          <rect x="10" y="65" width="25" height="25" fill="#1a1a2e" />
                          <rect x="15" y="70" width="15" height="15" fill="#fff" />
                          <rect x="18" y="73" width="9" height="9" fill="#1a1a2e" />
                          <rect x="40" y="10" width="5" height="5" fill="#1a1a2e" />
                          <rect x="50" y="15" width="5" height="5" fill="#1a1a2e" />
                          <rect x="55" y="20" width="5" height="5" fill="#1a1a2e" />
                          <rect x="40" y="40" width="5" height="5" fill="#1a1a2e" />
                          <rect x="50" y="45" width="5" height="5" fill="#1a1a2e" />
                          <rect x="45" y="55" width="5" height="5" fill="#1a1a2e" />
                          <rect x="65" y="40" width="5" height="5" fill="#1a1a2e" />
                          <rect x="75" y="45" width="5" height="5" fill="#1a1a2e" />
                          <rect x="85" y="50" width="5" height="5" fill="#1a1a2e" />
                          <rect x="40" y="65" width="5" height="5" fill="#1a1a2e" />
                          <rect x="55" y="70" width="5" height="5" fill="#1a1a2e" />
                          <rect x="45" y="80" width="5" height="5" fill="#1a1a2e" />
                          <rect x="65" y="65" width="5" height="5" fill="#1a1a2e" />
                          <rect x="80" y="70" width="5" height="5" fill="#1a1a2e" />
                          <rect x="75" y="85" width="5" height="5" fill="#1a1a2e" />
                          <rect x="90" y="75" width="5" height="5" fill="#1a1a2e" />
                        </svg>
                      </div>
                      <div className="getpro-upi-id">marketing@upi</div>
                    </div>
                    
                    <div className="getpro-steps-section">
                      <h4>Steps</h4>
                      {paymentStep === "scan" && (
                        <div className="getpro-steps">
                          <div className="step-item active">
                            <span className="step-num">1</span>
                            <span>Scan QR with UPI app</span>
                          </div>
                          <div className="step-item">
                            <span className="step-num">2</span>
                            <span>Pay {price}</span>
                          </div>
                          <div className="step-item">
                            <span className="step-num">3</span>
                            <span>Upload screenshot</span>
                          </div>
                        </div>
                      )}
                      {paymentStep === "upload" && (
                        <div className="getpro-steps">
                          <div className="step-item done">
                            <span className="step-num">✓</span>
                            <span>Scanned QR</span>
                          </div>
                          <div className="step-item done">
                            <span className="step-num">✓</span>
                            <span>Payment done</span>
                          </div>
                          <div className="step-item active">
                            <span className="step-num">3</span>
                            <span>Upload screenshot</span>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="getpro-payment-right">
                    <div className="getpro-billing-toggle">
                      <button
                        className={billingCycle === "monthly" ? "active" : ""}
                        onClick={() => setBillingCycle("monthly")}
                      >
                        Monthly
                      </button>
                      <button
                        className={billingCycle === "yearly" ? "active" : ""}
                        onClick={() => setBillingCycle("yearly")}
                      >
                        Yearly <span className="getpro-save-badge">-25%</span>
                      </button>
                    </div>
                    
                    <div className="getpro-price-display">
                      <span className="getpro-price">{price}</span>
                      <span className="getpro-price-note">{priceNote}</span>
                    </div>
                    
                    <div className="getpro-features">
                      <div className="getpro-feature"><span>💯</span> 100 runs/month</div>
                      <div className="getpro-feature"><span>🤖</span> All 24 agents</div>
                      <div className="getpro-feature"><span>🎯</span> Priority support</div>
                    </div>
                    
                    {paymentStep === "scan" && (
                      <button className="getpro-btn-primary" onClick={() => setPaymentStep("upload")}>
                        I&apos;ve Paid - Upload Screenshot →
                      </button>
                    )}
                    
                    {paymentStep === "upload" && (
                      <div className="getpro-upload-section">
                        <input
                          ref={fileInputRef}
                          type="file"
                          accept="image/*"
                          onChange={handleScreenshotUpload}
                          className="getpro-screenshot-input"
                        />
                        {screenshot && <p className="screenshot-preview">📎 {screenshot.name}</p>}
                        {error && <p className="getpro-error">{error}</p>}
                        <button 
                          className="getpro-btn-primary" 
                          onClick={handleSubmitScreenshot}
                          disabled={loading || !screenshot}
                        >
                          {loading ? "Submitting..." : "Submit Payment Proof"}
                        </button>
                      </div>
                    )}
                    
                    <div className="getpro-refund-policy">
                      <h4>💰 Refund Policy</h4>
                      <p>100% refund: ≤7 days &amp; ≤10 runs</p>
                      <p>50% refund: ≤15 days &amp; ≤50 runs</p>
                    </div>
                  </div>
                </div>
                
                <button className="getpro-btn-back" onClick={() => setPaymentStep("auth")}>
                  ← Back
                </button>
                
                <p className="getpro-secure">
                  <span>🔒</span> Secure payment • Cancel anytime
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export function AuthModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const [mode, setMode] = useState<"login" | "signup">("signup");
  const [email, setEmail] = useState("");
  const [password, setPasswordState] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  
  if (!isOpen) return null;
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    
    try {
      if (mode === "signup") {
        if (!name.trim() || !email.includes("@") || !password) {
          setError("Please fill in all fields");
          setLoading(false);
          return;
        }
        const result = await signUp(name, email, password);
        if (result.success) {
          onClose();
          window.location.reload();
        } else {
          setError(result.error || "Signup failed");
        }
      } else {
        if (!email.includes("@") || !password) {
          setError("Please fill in all fields");
          setLoading(false);
          return;
        }
        const result = await login(email, password);
        if (result.success) {
          onClose();
          window.location.reload();
        } else {
          setError(result.error || "Login failed");
        }
      }
    } catch (err) {
      setError("Something went wrong");
    }
    setLoading(false);
  };
  
  return (
    <div className="getpro-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="getpro-modal getpro-auth-modal">
        <button className="getpro-close" onClick={onClose}>×</button>
        
        <h2>{mode === "signup" ? "Create Account" : "Welcome Back"}</h2>
        <p className="getpro-modal-subtitle">Free account • No credit card required</p>
        
        <form onSubmit={handleSubmit}>
          {mode === "signup" && (
            <div className="getpro-field">
              <label>Your Name</label>
              <input type="text" placeholder="Priya Sharma" value={name} onChange={(e) => setName(e.target.value)} />
            </div>
          )}
          
          <div className="getpro-field">
            <label>Email</label>
            <input type="email" placeholder="priya@company.com" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          
          <div className="getpro-field">
            <label>Password</label>
            <input type="password" placeholder="Enter password" value={password} onChange={(e) => setPasswordState(e.target.value)} />
          </div>
          
          {error && <p className="getpro-error">{error}</p>}
          
          <button type="submit" className="getpro-btn-primary" disabled={loading}>
            {loading ? "..." : mode === "signup" ? "Create Free Account" : "Log In"}
          </button>
        </form>
        
        <p className="getpro-switch">
          {mode === "signup" ? "Already have an account?" : "New here?"}
          <button type="button" onClick={() => setMode(mode === "signup" ? "login" : "signup")}>
            {mode === "signup" ? "Log in" : "Sign up"}
          </button>
        </p>
      </div>
    </div>
  );
}
