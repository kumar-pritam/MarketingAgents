"use client";

const BASE_URL = process.env.NEXT_PUBLIC_APP_URL || "https://marketingagents.ai";

export function HomepageJsonLd() {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    name: "MarketingAgents.ai",
    description:
      "AI-powered marketing intelligence platform with 24 specialist agents for competitor analysis, content creation, SEO optimization, and more.",
    url: BASE_URL,
    applicationCategory: "BusinessApplication",
    operatingSystem: "Web",
    offers: {
      "@type": "Offer",
      price: "1000",
      priceCurrency: "INR",
      description: "Monthly subscription for Pro access",
    },
    aggregateRating: {
      "@type": "AggregateRating",
      ratingValue: "4.8",
      ratingCount: "127",
    },
    provider: {
      "@type": "Organization",
      name: "MarketingAgents",
      url: BASE_URL,
    },
    potentialAction: {
      "@type": "UseAction",
      target: {
        "@type": "EntryPoint",
        urlTemplate: `${BASE_URL}/agents`,
      },
      name: "Try Marketing Agents",
    },
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
    />
  );
}

export function OrganizationJsonLd() {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: "MarketingAgents",
    description:
      "AI-powered marketing intelligence platform helping businesses automate competitor analysis, content creation, and marketing optimization.",
    url: BASE_URL,
    logo: `${BASE_URL}/icon-192.png`,
    sameAs: [
      "https://twitter.com/marketingagents",
      "https://linkedin.com/company/marketingagents",
    ],
    contactPoint: {
      "@type": "ContactPoint",
      contactType: "customer support",
      email: "support@marketingagents.ai",
    },
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
    />
  );
}
