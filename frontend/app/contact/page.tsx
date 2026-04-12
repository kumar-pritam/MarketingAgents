"use client";

import { useState } from "react";
import Link from "next/link";
import type { Route } from "next";

export default function ContactPage() {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    subject: "",
    message: "",
  });
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
  };

  return (
    <div className="contact-page">
      <section className="hero-strip hero-premium">
        <div>
          <p className="hero-eyebrow">Contact & Feedback</p>
          <h1>We&apos;d love to hear from you</h1>
          <p className="hero-subtext">
            Have questions, feedback, or need support? Drop us a message and we&apos;ll get back to you shortly.
          </p>
        </div>
      </section>

      <section className="container" style={{ maxWidth: "720px" }}>
        {submitted ? (
          <div className="success-message">
            <div className="success-icon">✓</div>
            <h2>Message sent!</h2>
            <p>Thank you for reaching out. We&apos;ll get back to you within 24-48 hours.</p>
            <button onClick={() => setSubmitted(false)} className="btn btn-secondary">
              Send another message
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="contact-form">
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="name">Name</label>
                <input
                  type="text"
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                  placeholder="Your name"
                />
              </div>
              <div className="form-group">
                <label htmlFor="email">Email</label>
                <input
                  type="email"
                  id="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                  placeholder="you@company.com"
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="subject">Subject</label>
              <select
                id="subject"
                value={formData.subject}
                onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                required
              >
                <option value="">Select a topic</option>
                <option value="feedback">General Feedback</option>
                <option value="bug">Report a Bug</option>
                <option value="feature">Feature Request</option>
                <option value="support">Technical Support</option>
                <option value="business">Business Inquiry</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="message">Message</label>
              <textarea
                id="message"
                value={formData.message}
                onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                required
                placeholder="Tell us what's on your mind..."
                rows={6}
              />
            </div>

            <button type="submit" className="btn btn-primary">
              Send Message
            </button>
          </form>
        )}
      </section>

      <style>{`
        .contact-page {
          padding-bottom: 60px;
        }
        .contact-form {
          background: #fff;
          border: 1px solid #dde0e8;
          border-radius: 12px;
          padding: 32px;
          margin-bottom: 40px;
        }
        .form-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 20px;
        }
        .form-group {
          margin-bottom: 20px;
        }
        .form-group label {
          display: block;
          font-size: 13px;
          font-weight: 500;
          color: #374151;
          margin-bottom: 6px;
        }
        .form-group input,
        .form-group select,
        .form-group textarea {
          width: 100%;
          padding: 12px 14px;
          border: 1px solid #dde0e8;
          border-radius: 8px;
          font-size: 14px;
          font-family: inherit;
          transition: border-color 0.2s, box-shadow 0.2s;
        }
        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
          outline: none;
          border-color: #4f6ef7;
          box-shadow: 0 0 0 3px rgba(79, 110, 247, 0.1);
        }
        .form-group textarea {
          resize: vertical;
        }
        .success-message {
          text-align: center;
          padding: 60px 20px;
          background: #fff;
          border: 1px solid #dde0e8;
          border-radius: 12px;
        }
        .success-icon {
          width: 64px;
          height: 64px;
          border-radius: 50%;
          background: #e6fbf7;
          color: #00b894;
          font-size: 28px;
          display: flex;
          align-items: center;
          justify-content: center;
          margin: 0 auto 20px;
        }
        .success-message h2 {
          margin: 0 0 10px;
          color: #0f0f1a;
        }
        .success-message p {
          color: #6b7280;
          margin-bottom: 24px;
        }
        .contact-alternatives {
          text-align: center;
        }
        .contact-alternatives h3 {
          font-size: 16px;
          color: #0f0f1a;
          margin-bottom: 20px;
        }
        .alternatives-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 16px;
        }
        .alt-card {
          background: #fff;
          border: 1px solid #dde0e8;
          border-radius: 10px;
          padding: 20px;
          text-align: center;
        }
        .alt-icon {
          font-size: 24px;
          display: block;
          margin-bottom: 8px;
        }
        .alt-card strong {
          display: block;
          font-size: 14px;
          color: #0f0f1a;
          margin-bottom: 4px;
        }
        .alt-card a {
          font-size: 13px;
          color: #4f6ef7;
        }
        .btn-secondary {
          background: #fff;
          border: 1px solid #dde0e8;
          color: #0f0f1a;
        }
        @media (max-width: 640px) {
          .form-row {
            grid-template-columns: 1fr;
          }
          .alternatives-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
}