import "./globals.css";
import type { ReactNode } from "react";
import type { Metadata } from "next";
import Script from "next/script";
import { AppChrome } from "../components/AppChrome";
import { GlobalModalProvider } from "../components/ConfirmModal";
import { ToastContainer } from "../components/Toast";
import { ErrorBoundary } from "../components/ErrorBoundary";
import { NetworkStatusBanner } from "../hooks/useNetworkStatus";
import { OrganizationJsonLd } from "../components/JsonLd";
import { CookieConsent } from "../components/CookieConsent";

const BASE_URL = process.env.NEXT_PUBLIC_APP_URL || "https://marketingagents.ai";
const GA_ID = process.env.NEXT_PUBLIC_GA_ID;

export const metadata: Metadata = {
  metadataBase: new URL(BASE_URL),
  title: {
    default: "MarketingAgents.ai - AI-Powered Marketing Intelligence",
    template: "%s | MarketingAgents.ai",
  },
  description:
    "24 specialist AI agents for competitor intelligence, content creation, SEO optimization, and marketing automation. Transform your marketing with AI.",
  keywords: [
    "marketing AI",
    "AI agents",
    "competitor analysis",
    "content marketing",
    "SEO optimization",
    "marketing automation",
    "AI marketing tools",
    "business intelligence",
  ],
  authors: [{ name: "MarketingAgents" }],
  creator: "MarketingAgents",
  publisher: "MarketingAgents",
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: BASE_URL,
    siteName: "MarketingAgents.ai",
    title: "MarketingAgents.ai - AI-Powered Marketing Intelligence",
    description:
      "24 specialist AI agents for competitor intelligence, content creation, SEO optimization, and marketing automation.",
    images: [
      {
        url: `${BASE_URL}/og-image.png`,
        width: 1200,
        height: 630,
        alt: "MarketingAgents.ai",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "MarketingAgents.ai - AI-Powered Marketing Intelligence",
    description:
      "24 specialist AI agents for competitor intelligence, content creation, SEO optimization, and marketing automation.",
    images: [`${BASE_URL}/og-image.png`],
    creator: "@marketingagents",
  },
  alternates: {
    canonical: BASE_URL,
  },
  icons: {
    icon: [
      { url: "/favicon.ico" },
      { url: "/icon-192.png", sizes: "192x192", type: "image/png" },
      { url: "/icon-512.png", sizes: "512x512", type: "image/png" },
    ],
    apple: [{ url: "/apple-touch-icon.png" }],
  },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        <OrganizationJsonLd />
        {GA_ID && (
          <>
            <Script
              id="ga-init"
              strategy="lazyOnload"
              dangerouslySetInnerHTML={{
                __html: `
                  window.dataLayer = window.dataLayer || [];
                  function gtag(){dataLayer.push(arguments);}
                  gtag('js', new Date());
                  gtag('config', '${GA_ID}', { send_page_view: false });
                `,
              }}
            />
          </>
        )}
      </head>
      <body suppressHydrationWarning>
        <NetworkStatusBanner />
        <ToastContainer />
        <ErrorBoundary>
          <GlobalModalProvider>
            <AppChrome>{children}</AppChrome>
          </GlobalModalProvider>
        </ErrorBoundary>
        <CookieConsent />
        {GA_ID && (
          <Script
            src={`https://www.googletagmanager.com/gtag/js?id=${GA_ID}`}
            strategy="lazyOnload"
          />
        )}
      </body>
    </html>
  );
}
