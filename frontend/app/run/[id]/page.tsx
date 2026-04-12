"use client";

import Link from "next/link";
import type { Route } from "next";
import { useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { apiGet, apiPost } from "../../../lib/api";
import { canRun, getUserStatus, incrementRuns } from "../../../lib/usageTracking";
import { showConfirm, showAlert } from "../../../components/ConfirmModal";

type AgentSpec = {
  id: string;
  name: string;
  summary: string;
  description: string;
  category: string;
};

type IntegrationState = { provider: string; connected: boolean; scopes: string[]; connected_at: string | null };
type WorkspaceSummary = {
  workspace_id: string;
  workspace_name: string;
  brand_name: string;
  website: string;
  industry: string;
  category?: string | null;
  geography?: string | null;
  positioning?: string | null;
  additional_details?: string | null;
  brand_summary?: string | null;
  brand_analysis?: Record<string, string | number>;
};

type PrimaryConcern = "Awareness" | "Sentiment" | "AI Visibility" | "Share of Voice" | "All";
type Goal = "Awareness" | "Consideration" | "Recommendation" | "All";
type RunState = "idle" | "loading" | "complete";

type FieldErrors = {
  brandName?: string;
  brandContext?: string;
  competitors?: string;
  categoryKeywords?: string;
  timeWindow?: string;
  primaryConcern?: string;
  queries?: string;
  goal?: string;
};

const MY_BRAND_WORKSPACE_KEY = "marketing_agents_my_brand_workspace_v1";

const PROVIDERS = [
  { id: "gsc", label: "Google Search Console", value: "Keyword performance data", icon: "🔎" },
  { id: "ga4", label: "Google Analytics 4", value: "Traffic and engagement signals", icon: "📊" },
  { id: "google_ads", label: "Google Ads", value: "Paid search visibility data", icon: "📣" },
] as const;

type AgentInputType = "text" | "textarea" | "url" | "dropdown" | "multiselect";

type AgentInput = {
  key: string;
  label: string;
  type: AgentInputType;
  required?: boolean;
  placeholder?: string;
  helper?: string;
  options?: string[];
  multilineOptions?: string[];
};

type AgentInputConfig = {
  inputs: AgentInput[];
  workspace_mapping?: Record<string, string>;
  expected_output?: string[];
  progress_messages?: string[];
};

const AGENT_INPUT_CONFIGS: Record<string, AgentInputConfig> = {
  competitive_intelligence_agent: {
    workspace_mapping: { competitors: "competitors" },
    expected_output: ["Positioning Map", "Messaging Themes", "Recent Moves", "Where You Win", "Where Vulnerable", "Strategic Move"],
    progress_messages: ["Mapping competitor positioning across channels...", "Analyzing messaging themes and campaigns...", "Identifying strategic opportunities...", "Synthesizing competitive intelligence..."],
    inputs: [
      { key: "competitors", label: "Competitors", type: "textarea", required: true, placeholder: "Nykaa, Purplle, Myntra Beauty", helper: "List the competitors to analyze" },
      { key: "analysis_focus", label: "Analysis Focus", type: "multiselect", required: true, options: ["Positioning", "Campaigns", "Product launches", "Pricing"], multilineOptions: ["Positioning", "Campaigns", "Product launches", "Pricing"], helper: "Select what to focus on" },
      { key: "time_window", label: "Time Window", type: "dropdown", required: true, options: ["Last 30 days", "Last 90 days", "Last 6 months"], placeholder: "Select time window", helper: "Analysis period" },
      { key: "strategic_question", label: "Strategic Question (Optional)", type: "textarea", required: false, placeholder: "Where are competitors investing that we are not?", helper: "Optional specific question" },
    ],
  },
  content_agent: {
    workspace_mapping: { target_audience: "target_audience" },
    expected_output: ["Headline Variants", "Body Copy", "CTA Variants", "Creative Rationale"],
    progress_messages: ["Analyzing campaign brief and audience...", "Generating headline variants...", "Crafting body copy for each format...", "Developing CTAs and rationale..."],
    inputs: [
      { key: "content_type", label: "Content Type", type: "multiselect", required: true, options: ["Email", "Ad copy", "Push", "Social", "SMS"], multilineOptions: ["Email", "Ad copy", "Push", "Social", "SMS"], helper: "Select content types to generate" },
      { key: "target_audience", label: "Target Audience", type: "text", required: true, placeholder: "Urban women 25-40, health-conscious", helper: "Describe your target audience" },
      { key: "campaign_objective", label: "Campaign Objective", type: "textarea", required: true, placeholder: "Drive app downloads during festive season", helper: "What do you want to achieve?" },
      { key: "tone", label: "Tone", type: "dropdown", required: true, options: ["Professional", "Conversational", "Bold", "Witty"], placeholder: "Select tone", helper: "Select copy tone" },
      { key: "mandatories", label: "Mandatories (Optional)", type: "textarea", required: false, placeholder: "Include offer code FEST25", helper: "Required elements to include" },
    ],
  },
  brand_equity_tracker_agent: {
    workspace_mapping: { competitors: "competitors", category_keywords: "category" },
    expected_output: ["Health Score (0-100)", "Pulse Summary", "Top Risk", "Top Opportunity", "AI Visibility", "Brand Associations", "Top 3 Actions"],
    progress_messages: ["Gathering brand awareness signals...", "Analyzing sentiment across channels...", "Measuring share of voice vs competitors...", "Assessing AI visibility...", "Synthesizing brand health score..."],
    inputs: [
      { key: "competitors", label: "Competitors", type: "textarea", required: true, placeholder: "Pepsi, Thums Up", helper: "List your competitors" },
      { key: "category_keywords", label: "Category Keywords", type: "textarea", required: true, placeholder: "cola, soft drink, refreshment", helper: "Keywords for your category" },
      { key: "time_window", label: "Time Window", type: "dropdown", required: true, options: ["Last 30 days", "Last 90 days", "Last 6 months"], placeholder: "Select time window", helper: "Analysis period" },
      { key: "primary_concern", label: "Primary Concern", type: "dropdown", required: true, options: ["Awareness", "Sentiment", "AI Visibility", "Share of Voice", "All"], placeholder: "Select focus", helper: "Primary dimension to focus on" },
    ],
  },
  geo_agent: {
    workspace_mapping: { competitors: "competitors" },
    expected_output: ["AI Share of Voice", "Query Visibility", "Representation Accuracy", "Sentiment in AI", "Top GEO Actions", "GEO Health Score"],
    progress_messages: ["Searching AI platforms for brand mentions...", "Analyzing visibility across ChatGPT, Gemini, Perplexity...", "Measuring AI share of voice vs competitors...", "Identifying content gaps...", "Generating GEO recommendations..."],
    inputs: [
      { key: "competitors", label: "Competitors", type: "textarea", required: true, placeholder: "boAt, Noise", helper: "List your competitors" },
      { key: "category_queries", label: "Category Queries", type: "textarea", required: true, placeholder: "best wireless earphones under 2000", helper: "Queries to test AI visibility" },
      { key: "ai_platforms", label: "AI Platforms", type: "multiselect", required: true, options: ["ChatGPT", "Gemini", "Perplexity", "Claude", "Copilot"], multilineOptions: ["ChatGPT", "Gemini", "Perplexity", "Claude", "Copilot"], helper: "Select AI platforms to analyze" },
      { key: "visibility_goal", label: "Visibility Goal", type: "dropdown", required: true, options: ["Awareness", "Consideration", "Recommendation", "All"], placeholder: "Select goal", helper: "Calibration goal" },
    ],
  },
  creative_agent: {
    workspace_mapping: {},
    expected_output: ["Territory 1", "Territory 2", "Territory 3", "Core Idea", "Sample Headlines", "Visual Direction"],
    progress_messages: ["Analyzing campaign brief...", "Generating creative territories...", "Developing core ideas and insights...", "Crafting sample headlines...", "Defining visual direction..."],
    inputs: [
      { key: "campaign_brief", label: "Campaign Brief", type: "textarea", required: true, placeholder: "Objective, audience, key message", helper: "Describe your campaign brief" },
      { key: "format", label: "Format", type: "multiselect", required: true, options: ["TVC", "Digital", "OOH", "Social", "Print"], multilineOptions: ["TVC", "Digital", "OOH", "Social", "Print"], helper: "Select output formats" },
      { key: "creative_territories", label: "Creative Territories", type: "dropdown", required: true, options: ["2", "3"], placeholder: "Number of territories", helper: "How many directions?" },
      { key: "reference_brands", label: "Reference Brands (Optional)", type: "text", required: false, placeholder: "Dove, Tanishq - emotional storytelling", helper: "Brands for creative reference" },
    ],
  },
  brand_voice_guardian_agent: {
    workspace_mapping: { voice_guidelines: "positioning" },
    expected_output: ["Compliance Rating", "Flagged Lines", "What Works", "Recommendation"],
    progress_messages: ["Analyzing content against voice guidelines...", "Identifying off-brand phrases...", "Generating compliance report...", "Creating rewrites..."],
    inputs: [
      { key: "voice_guidelines", label: "Voice Guidelines", type: "textarea", required: true, placeholder: "Paste tone doc or bullet summary", helper: "Your brand voice guidelines" },
      { key: "content_to_audit", label: "Content to Audit", type: "textarea", required: true, placeholder: "Ad copy, email, social post", helper: "Content to review" },
      { key: "content_type", label: "Content Type", type: "dropdown", required: true, options: ["Social", "Email", "Ad", "Landing page", "Press release"], placeholder: "Select type", helper: "Type of content" },
      { key: "strictness", label: "Strictness", type: "dropdown", required: true, options: ["Strict", "Balanced", "Light touch"], placeholder: "Select level", helper: "Audit strictness level" },
    ],
  },
  campaign_brief_generator_agent: {
    workspace_mapping: { target_audience: "target_audience" },
    expected_output: ["Campaign Objective", "Consumer Insight", "Single Minded Proposition", "Reasons to Believe", "Channel Strategy", "Success Metrics", "Creative Territories"],
    progress_messages: ["Analyzing business objective...", "Researching target audience insights...", "Developing consumer insight...", "Crafting single minded proposition...", "Defining channel strategy and metrics..."],
    inputs: [
      { key: "business_objective", label: "Business Objective", type: "textarea", required: true, placeholder: "Drive 20% increase in trial sign-ups in Q3", helper: "What business goal?" },
      { key: "target_audience", label: "Target Audience", type: "textarea", required: true, placeholder: "Urban women 25-40, health-conscious, SEC A", helper: "Who are you targeting?" },
      { key: "budget_range", label: "Budget Range", type: "dropdown", required: true, options: ["<10L", "10-50L", "50L-1Cr", "1Cr+"], placeholder: "Select budget", helper: "Campaign budget" },
      { key: "campaign_duration", label: "Campaign Duration", type: "text", required: true, placeholder: "e.g. 6 weeks", helper: "How long?" },
      { key: "channels", label: "Channels", type: "multiselect", required: true, options: ["TV", "Digital", "OOH", "Influencer", "Social"], multilineOptions: ["TV", "Digital", "OOH", "Influencer", "Social"], helper: "Select channels" },
      { key: "mandatories", label: "Mandatories (Optional)", type: "textarea", required: false, placeholder: "Must feature new variant, festive theme", helper: "Required elements" },
    ],
  },
  landing_page_optimization_agent: {
    workspace_mapping: {},
    expected_output: ["Conversion Audit Score", "Above the Fold Analysis", "Friction Points", "Copy Improvements", "Structural Recommendations", "Quick Win"],
    progress_messages: ["Fetching landing page content...", "Analyzing conversion barriers...", "Identifying friction points...", "Generating copy improvements...", "Developing structural recommendations..."],
    inputs: [
      { key: "page_url", label: "Page URL", type: "url", required: true, placeholder: "www.brand.com/product", helper: "Landing page to audit" },
      { key: "conversion_goal", label: "Conversion Goal", type: "text", required: true, placeholder: "Free trial sign-up", helper: "What action?" },
      { key: "target_audience", label: "Target Audience", type: "text", required: true, placeholder: "B2B marketers, mid-market", helper: "Who should convert?" },
      { key: "current_conversion_issue", label: "Known Issue (Optional)", type: "textarea", required: false, placeholder: "High bounce on hero section", helper: "Any known problems?" },
    ],
  },
  persona_research_agent: {
    workspace_mapping: { product_category: "category", target_segment: "target_segment" },
    expected_output: ["Persona Snapshot", "Motivations", "Frustrations", "Current Behaviour", "Switching Triggers", "Voice of Consumer", "Channels", "Buying Journey"],
    progress_messages: ["Researching consumer signals from reviews...", "Analyzing Reddit and forum discussions...", "Building persona motivations and frustrations...", "Mapping buying journey and touchpoints...", "Synthesizing persona profile..."],
    inputs: [
      { key: "product_category", label: "Product Category", type: "text", required: true, placeholder: "Term life insurance", helper: "What category?" },
      { key: "target_segment", label: "Target Segment", type: "text", required: true, placeholder: "First-time buyers, 28-35, urban", helper: "Who are you targeting?" },
      { key: "geography", label: "Geography", type: "dropdown", required: true, options: ["India", "US", "UK", "SEA", "Global"], placeholder: "Select geography", helper: "Where?" },
      { key: "pain_point", label: "Pain Point (Optional)", type: "text", required: false, placeholder: "Price sensitivity vs. trust", helper: "Specific pain point to explore" },
    ],
  },
  social_listening_agent: {
    workspace_mapping: {},
    expected_output: ["Sentiment Score", "Trending Themes", "Emerging Narratives", "Competitor Sentiment", "Crisis Signals", "Engagement Opportunities"],
    progress_messages: ["Monitoring social mentions...", "Analyzing sentiment across platforms...", "Identifying trending themes...", "Detecting emerging narratives...", "Scanning for crisis signals..."],
    inputs: [
      { key: "keywords_to_track", label: "Keywords to Track", type: "textarea", required: true, placeholder: "Swift, Maruti Swift, #DriveYourStory", helper: "Brand terms to monitor" },
      { key: "competitors", label: "Competitors", type: "textarea", required: true, placeholder: "Hyundai i20, Tata Altroz", helper: "Competitor brands" },
      { key: "time_window", label: "Time Window", type: "dropdown", required: true, options: ["Last 7 days", "Last 30 days", "Last 90 days"], placeholder: "Select time window", helper: "Analysis period" },
      { key: "platforms", label: "Platforms", type: "multiselect", required: true, options: ["Twitter/X", "Reddit", "Instagram", "LinkedIn", "YouTube"], multilineOptions: ["Twitter/X", "Reddit", "Instagram", "LinkedIn", "YouTube"], helper: "Where to listen?" },
    ],
  },
  seo_content_gap_agent: {
    workspace_mapping: { brand_url: "website", category_keywords: "category" },
    expected_output: ["Content Gap Analysis", "Keyword Opportunities", "Competitor Content Strengths", "Priority Topics", "Content Recommendations"],
    progress_messages: ["Analyzing competitor content strategies...", "Identifying keyword gaps and opportunities...", "Mapping content gaps by funnel stage...", "Generating content recommendations..."],
    inputs: [
      { key: "brand_url", label: "Brand URL", type: "url", required: true, placeholder: "www.mamaearth.in", helper: "Your website" },
      { key: "competitor_urls", label: "Competitor URLs", type: "textarea", required: true, placeholder: "www.mcaffeine.com, www.plumgoodness.com", helper: "Competitor websites" },
      { key: "category_keywords", label: "Category Keywords", type: "textarea", required: true, placeholder: "natural skincare, paraben-free moisturiser", helper: "Keywords to target" },
      { key: "funnel_focus", label: "Funnel Focus", type: "dropdown", required: true, options: ["Top", "Mid", "Bottom", "All"], placeholder: "Select funnel stage", helper: "Which stage to focus on?" },
      { key: "content_formats", label: "Content Formats", type: "multiselect", required: true, options: ["Blog", "Video", "Landing pages", "FAQs"], multilineOptions: ["Blog", "Video", "Landing pages", "FAQs"], helper: "Output formats" },
    ],
  },
  localisation_cultural_fit_agent: {
    workspace_mapping: {},
    expected_output: ["Cultural Sensitivity Score", "Flagged Elements", "Cultural Equivalents", "Tone Adaptation", "Local Recommendations"],
    progress_messages: ["Analyzing campaign copy for cultural elements...", "Checking religious and social sensitivities...", "Finding cultural equivalents...", "Generating localisation recommendations..."],
    inputs: [
      { key: "campaign_copy", label: "Campaign Copy", type: "textarea", required: true, placeholder: "Headline, body, CTA", helper: "Copy to audit" },
      { key: "source_market", label: "Source Market", type: "dropdown", required: true, options: ["US", "UK", "India", "Global"], placeholder: "Where from?", helper: "Original market" },
      { key: "target_market", label: "Target Market", type: "text", required: true, placeholder: "Tamil Nadu, India or Saudi Arabia", helper: "Where to?" },
      { key: "campaign_format", label: "Campaign Format", type: "dropdown", required: true, options: ["Digital", "OOH", "TV", "Social", "Email"], placeholder: "Select format", helper: "Campaign format" },
      { key: "sensitivity_areas", label: "Sensitivity Areas (Optional)", type: "multiselect", required: false, options: ["Religion", "Gender", "Humour", "Political", "Food"], multilineOptions: ["Religion", "Gender", "Humour", "Political", "Food"], helper: "Areas to check" },
    ],
  },
  customer_review_intelligence_agent: {
    workspace_mapping: { product_name: "category" },
    expected_output: ["Review Sentiment Breakdown", "Top Praise Points", "Top Complaints", "Unmet Needs", "Comparison vs Competitor", "Actionable Insights"],
    progress_messages: ["Gathering reviews from multiple platforms...", "Analyzing sentiment patterns...", "Identifying unmet needs and churn signals...", "Comparing with competitor reviews...", "Generating actionable insights..."],
    inputs: [
      { key: "product_name", label: "Product / SKU", type: "text", required: true, placeholder: "Himalaya Ashwagandha Tablets", helper: "Product to analyze" },
      { key: "platforms", label: "Platforms", type: "multiselect", required: true, options: ["Amazon", "G2", "Trustpilot", "App Store", "Reddit"], multilineOptions: ["Amazon", "G2", "Trustpilot", "App Store", "Reddit"], helper: "Where to search?" },
      { key: "focus_area", label: "Focus Area", type: "dropdown", required: true, options: ["Unmet needs", "Churn signals", "Sentiment", "All"], placeholder: "Select focus", helper: "What to prioritize?" },
      { key: "competitor_product", label: "Competitor to Compare (Optional)", type: "text", required: false, placeholder: "Dabur Shilajit", helper: "Optional competitor" },
    ],
  },
  experimentation_agent: {
    workspace_mapping: {},
    expected_output: ["Test Hypothesis", "Test Variants", "Success Metrics", "Statistical Significance", "Implementation Notes"],
    progress_messages: ["Analyzing your hypothesis...", "Designing test variants...", "Defining success metrics...", "Generating implementation notes...", "Ensuring statistical rigor..."],
    inputs: [
      { key: "page_or_asset", label: "Page or Asset", type: "text", required: true, placeholder: "Homepage hero or Email subject line", helper: "What to test?" },
      { key: "hypothesis", label: "Hypothesis", type: "textarea", required: true, placeholder: "Benefit-led headline will outperform feature-led", helper: "What do you expect?" },
      { key: "conversion_goal", label: "Conversion Goal", type: "text", required: true, placeholder: "Sign-up clicks", helper: "Success metric" },
      { key: "audience_segment", label: "Audience Segment (Optional)", type: "text", required: false, placeholder: "Returning visitors, mobile", helper: "Specific segment" },
    ],
  },
  retail_shelf_intelligence_agent: {
    workspace_mapping: { competitors: "competitors" },
    expected_output: ["Listing Score", "Price Positioning", "Review Summary", "Competitor Comparison", "Shelf Visibility", "Recommendations"],
    progress_messages: ["Scraping retail platform data...", "Analyzing product listings and reviews...", "Comparing shelf positioning...", "Generating competitive insights..."],
    inputs: [
      { key: "product_sku", label: "Product / SKU", type: "text", required: true, placeholder: "Tata Sampann Chana Dal 1kg", helper: "Product to analyze" },
      { key: "platform", label: "Platform", type: "dropdown", required: true, options: ["Amazon India", "Flipkart", "Blinkit", "Zepto", "BigBasket"], placeholder: "Select platform", helper: "Where to analyze?" },
      { key: "competitor_products", label: "Competitor Products", type: "textarea", required: true, placeholder: "Fortune Chana Dal, Aashirvaad Chana Dal", helper: "Competitor SKUs" },
      { key: "category_search_term", label: "Category Search Term", type: "text", required: true, placeholder: "chana dal 1kg", helper: "Search term to analyze" },
    ],
  },
  market_sizing_agent: {
    workspace_mapping: { product_category: "category" },
    expected_output: ["Total Addressable Market (TAM)", "Serviceable Addressable Market (SAM)", "Serviceable Obtainable Market (SOM)", "Growth Rate", "Key Drivers", "Assumptions"],
    progress_messages: ["Researching market data and reports...", "Analyzing industry trends...", "Calculating market size estimates...", "Validating assumptions...", "Generating market sizing model..."],
    inputs: [
      { key: "product_category", label: "Product Category", type: "text", required: true, placeholder: "Plant-based protein supplements", helper: "Category to size" },
      { key: "geography", label: "Geography", type: "dropdown", required: true, options: ["India", "US", "UK", "SEA", "Global"], placeholder: "Select geography", helper: "Where?" },
      { key: "market_stage", label: "Market Stage", type: "dropdown", required: true, options: ["Emerging", "Growing", "Mature"], placeholder: "Select stage", helper: "Market maturity" },
      { key: "sizing_purpose", label: "Sizing Purpose", type: "dropdown", required: true, options: ["Investor pitch", "Internal planning", "New market entry"], placeholder: "Select purpose", helper: "Why?" },
    ],
  },
  sales_enablement_agent: {
    workspace_mapping: {},
    expected_output: ["Battlecard Summary", "Competitor Weaknesses", "Your Strengths", "Talk Tracks", "Objection Handling", "Discovery Questions"],
    progress_messages: ["Researching competitor positioning...", "Analyzing win/loss patterns...", "Identifying competitive weaknesses...", "Generating battlecards and talk tracks..."],
    inputs: [
      { key: "competitor", label: "Competitor", type: "text", required: true, placeholder: "Salesforce Marketing Cloud", helper: "Competitor to battle" },
      { key: "product_feature", label: "Product / Feature", type: "text", required: true, placeholder: "AI-powered segmentation module", helper: "What to position?" },
      { key: "buyer_persona", label: "Buyer Persona", type: "text", required: true, placeholder: "VP Marketing, mid-market B2B SaaS", helper: "Who are you selling to?" },
      { key: "top_objection", label: "Top Objection (Optional)", type: "textarea", required: false, placeholder: "Competitor is cheaper and integrated", helper: "Common objection to handle" },
    ],
  },
  influencer_evaluation_agent: {
    workspace_mapping: {},
    expected_output: ["Influencer Profiles", "Authenticity Score", "Audience Quality", "Engagement Analysis", "Brand Fit", "Recommendations", "Red Flags"],
    progress_messages: ["Scanning influencer profiles...", "Analyzing engagement authenticity...", "Evaluating audience demographics...", "Checking brand alignment...", "Generating recommendations..."],
    inputs: [
      { key: "influencer_handles", label: "Influencer Handles", type: "textarea", required: true, placeholder: "@komal_pandey, @be_younicorn", helper: "Handles to evaluate" },
      { key: "platform", label: "Platform", type: "dropdown", required: true, options: ["Instagram", "YouTube", "LinkedIn", "X", "Moj"], placeholder: "Select platform", helper: "Primary platform" },
      { key: "campaign_objective", label: "Campaign Objective", type: "dropdown", required: true, options: ["Awareness", "Consideration", "Conversion", "Community"], placeholder: "Select objective", helper: "What for?" },
      { key: "budget_tier", label: "Budget Tier", type: "dropdown", required: true, options: ["Nano", "Micro", "Macro", "Mega"], placeholder: "Select tier", helper: "Influencer tier" },
      { key: "conflict_check", label: "Conflict Check (Optional)", type: "text", required: false, placeholder: "No competitor collabs in last 6 months", helper: "Conflict requirements" },
    ],
  },
  pr_narrative_agent: {
    workspace_mapping: {},
    expected_output: ["PR Narrative", "Angle", "Key Messages", "Target Outlets", "Story Arc", "Press Release Draft", "Media List"],
    progress_messages: ["Crafting PR narrative...", "Researching news hooks and angles...", "Developing key messages...", "Generating press release draft...", "Identifying target media outlets..."],
    inputs: [
      { key: "comms_objective", label: "Communications Objective", type: "textarea", required: true, placeholder: "Position as sustainability leader", helper: "What to achieve?" },
      { key: "story_type", label: "Story Type", type: "dropdown", required: true, options: ["Newsjacking", "Proactive pitch", "Thought leadership", "Crisis prep"], placeholder: "Select type", helper: "Type of story" },
      { key: "target_media", label: "Target Media (Optional)", type: "text", required: false, placeholder: "Economic Times, Mint, YourStory", helper: "Publications to target" },
      { key: "news_hook", label: "News Hook (Optional)", type: "text", required: false, placeholder: "World Environment Day, June 5", helper: "Timely hook" },
    ],
  },
  marketing_compliance_agent: {
    workspace_mapping: {},
    expected_output: ["Compliance Score", "Flagged Claims", "Risk Assessment", "Safe Alternatives", "Regulatory Notes", "Recommendations"],
    progress_messages: ["Analyzing content for compliance risks...", "Checking regulatory requirements...", "Identifying prohibited claims...", "Generating compliant alternatives..."],
    inputs: [
      { key: "content_to_audit", label: "Content to Audit", type: "textarea", required: true, placeholder: "Full ad copy or script", helper: "Content to review" },
      { key: "target_market", label: "Target Market", type: "dropdown", required: true, options: ["India", "US", "UK", "EU", "UAE"], placeholder: "Select market", helper: "Where will it run?" },
      { key: "sector", label: "Sector", type: "dropdown", required: true, options: ["BFSI", "Pharma", "F&B", "Edtech", "FMCG", "D2C", "General"], placeholder: "Select sector", helper: "Industry" },
      { key: "content_format", label: "Content Format", type: "dropdown", required: true, options: ["Digital ad", "TV", "Influencer post", "Email", "OOH"], placeholder: "Select format", helper: "Content type" },
      { key: "specific_concern", label: "Specific Concern (Optional)", type: "text", required: false, placeholder: "Is '100% natural' defensible?", helper: "Specific question" },
    ],
  },
  pricing_intelligence_agent: {
    workspace_mapping: { competitors: "competitors" },
    expected_output: ["Price Positioning Map", "Value Gap Analysis", "Competitive Price Points", "Sweet Spot Recommendation", "Pricing Strategy"],
    progress_messages: ["Researching competitor pricing...", "Analyzing price-to-feature ratios...", "Mapping competitive positioning...", "Generating pricing recommendations..."],
    inputs: [
      { key: "product_name", label: "Product", type: "text", required: true, placeholder: "Maruti Swift ZXI+", helper: "Product to analyze" },
      { key: "competitors", label: "Competitors", type: "textarea", required: true, placeholder: "Hyundai i20 Asta, Tata Altroz XZ+", helper: "Competitor products" },
      { key: "pricing_question", label: "Pricing Question", type: "textarea", required: true, placeholder: "Are we priced correctly for our feature set?", helper: "What to answer?" },
      { key: "market", label: "Market", type: "dropdown", required: true, options: ["India", "US", "UK", "SEA", "Global"], placeholder: "Select market", helper: "Where?" },
    ],
  },
  campaign_qa_agent: {
    workspace_mapping: { target_audience: "target_audience" },
    expected_output: ["Consistency Score", "Message Alignment", "Brand Voice Compliance", "Channel Fit", "Issue Flags", "Quick Fixes"],
    progress_messages: ["Analyzing campaign assets...", "Checking message consistency...", "Validating brand voice compliance...", "Identifying potential issues...", "Generating quick fixes..."],
    inputs: [
      { key: "campaign_assets", label: "Campaign Assets", type: "textarea", required: true, placeholder: "Paste all copy: ads, emails, social, OOH", helper: "All campaign copy" },
      { key: "campaign_objective", label: "Campaign Objective", type: "text", required: true, placeholder: "Drive festive sale sign-ups", helper: "What for?" },
      { key: "target_audience", label: "Target Audience", type: "text", required: true, placeholder: "Urban millennials, 25-35", helper: "Who?" },
      { key: "channels", label: "Channels", type: "multiselect", required: true, options: ["TV", "Digital", "OOH", "Social", "Email"], multilineOptions: ["TV", "Digital", "OOH", "Social", "Email"], helper: "Where will it run?" },
    ],
  },
  visual_identity_audit_agent: {
    workspace_mapping: {},
    expected_output: ["Visual Consistency Score", "Logo Usage", "Color Palette Analysis", "Typography Review", "Imagery Style", "Social Consistency", "Website Consistency", "Recommendations"],
    progress_messages: ["Analyzing brand website visuals...", "Scanning social media presence...", "Auditing logo usage...", "Checking color and typography consistency...", "Generating visual identity report..."],
    inputs: [
      { key: "brand_url", label: "Brand URL", type: "url", required: true, placeholder: "www.brand.com", helper: "Website to audit" },
      { key: "social_handles", label: "Social Handles", type: "text", required: true, placeholder: "@brandname on Instagram, LinkedIn", helper: "Social accounts" },
      { key: "visual_guidelines", label: "Visual Guidelines (Optional)", type: "textarea", required: false, placeholder: "Paste brand visual standards summary", helper: "Standards to check against" },
      { key: "audit_focus", label: "Audit Focus", type: "multiselect", required: true, options: ["Logo", "Color", "Typography", "Imagery", "Social", "Website"], multilineOptions: ["Logo", "Color", "Typography", "Imagery", "Social", "Website"], helper: "What to audit?" },
    ],
  },
  competitor_intelligence_legacy_agent: {
    workspace_mapping: {},
    expected_output: ["Competitor Overview", "Positioning Statement", "Key Campaigns", "Product Highlights", "Pricing Strategy", "Strategic Insights"],
    progress_messages: ["Researching competitor...", "Analyzing positioning strategy...", "Identifying key campaigns...", "Evaluating product and pricing...", "Generating strategic insights..."],
    inputs: [
      { key: "competitor", label: "Competitor", type: "text", required: true, placeholder: "Purplle", helper: "Single competitor" },
      { key: "focus", label: "Focus", type: "dropdown", required: true, options: ["Positioning", "Pricing", "Product", "Campaigns"], placeholder: "Select focus", helper: "What to analyze?" },
    ],
  },
};

function getAgentInputs(agentId: string): AgentInput[] {
  return AGENT_INPUT_CONFIGS[agentId]?.inputs || AGENT_INPUT_CONFIGS.geo_agent.inputs;
}

const AGENT_ICON: Record<string, string> = {
  geo_agent: "🌐",
  competitive_intelligence_agent: "🧭",
  content_agent: "✍️",
  creative_agent: "🎨",
  experimentation_agent: "🧪",
  landing_page_optimization_agent: "🚀",
  pricing_intelligence_agent: "💰",
  social_listening_agent: "👂",
  campaign_planner_agent: "📋",
  campaign_qa_agent: "🎯",
  brand_equity_tracker_agent: "🧬",
  brand_voice_guardian_agent: "🎙️",
  campaign_brief_generator_agent: "📝",
  persona_research_agent: "👤",
  seo_content_gap_agent: "🔎",
  localisation_cultural_fit_agent: "🌍",
  customer_review_intelligence_agent: "⭐",
  retail_shelf_intelligence_agent: "📦",
  market_sizing_agent: "📊",
  sales_enablement_agent: "⚔️",
  influencer_evaluation_agent: "📣",
  pr_narrative_agent: "📰",
  marketing_compliance_agent: "⚖️",
  visual_identity_audit_agent: "🖼️",
  competitor_intelligence_legacy_agent: "🧭",
};

const STATUS_MESSAGES = [
  "Gathering awareness and sentiment signals from public coverage...",
  "Estimating share of voice vs. competitors across media channels...",
  "Assessing AI / GEO visibility and representation accuracy...",
  "Synthesizing competitive moves and category risks...",
  "Crafting strategic recommendations for the CMO briefing...",
];

const SECTION_KEYS = [
  "brand_health_score",
  "pulse_summary",
  "biggest_risk",
  "biggest_opportunity",
  "ai_visibility_snapshot",
  "brand_associations",
  "top_3_actions",
] as const;
const BRAND_EQUITY_SECTION_KEYS = SECTION_KEYS;
const GENERAL_SECTION_KEYS = ["share_of_voice", "query_analysis", "representation", "sentiment", "recommendations", "geo_health"] as const;
type SectionKey = (typeof SECTION_KEYS)[number];

export default function AgentRunPage() {
  const params = useParams<{ id: string }>();
  const agentId = params.id;

  const [spec, setSpec] = useState<AgentSpec | null>(null);
  const [workspaces, setWorkspaces] = useState<WorkspaceSummary[]>([]);
  const [workspaceId, setWorkspaceId] = useState("");
  const [myBrandWorkspaceId, setMyBrandWorkspaceId] = useState<string>("");
  const [integrations, setIntegrations] = useState<Record<string, IntegrationState>>({});
  const [includedIntegrations, setIncludedIntegrations] = useState<Record<string, boolean>>({});

  const [brandName, setBrandName] = useState("");
  const [brandContext, setBrandContext] = useState("");
  const [additionalDetails, setAdditionalDetails] = useState("");
  const [competitors, setCompetitors] = useState("");
  const [queries, setQueries] = useState("");
  const [categoryKeywords, setCategoryKeywords] = useState("");
  const [timeWindow, setTimeWindow] = useState("Last 90 days");
  const [primaryConcern, setPrimaryConcern] = useState<PrimaryConcern>("All");
  const [goal, setGoal] = useState<Goal>("All");
  const [autoAddContext, setAutoAddContext] = useState(true);

  const [errors, setErrors] = useState<FieldErrors>({});
  const [runState, setRunState] = useState<RunState>("idle");
  const [revealedCount, setRevealedCount] = useState(0);
  const [statusIdx, setStatusIdx] = useState(0);
  const collapsedInit: Record<string, boolean> = {};
  const [brandEquityReportData, setBrandEquityReportData] = useState<any>(null); // State to hold the full report data from backend
  [...BRAND_EQUITY_SECTION_KEYS, ...GENERAL_SECTION_KEYS].forEach((key) => {
    collapsedInit[key] = false;
  });
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>(collapsedInit);
  const [activeStep, setActiveStep] = useState<1 | 2 | 3 | 4>(1);
  const [savedState, setSavedState] = useState<"idle" | "saving" | "saved">("idle");
  const [isAutoFilling, setIsAutoFilling] = useState(false);
  const [debugInfo, setDebugInfo] = useState<{source: string; missing_fields: string[]; llm_returned: any; filled_sections: string[]; error: string | null} | null>(null);
  const [showDebug, setShowDebug] = useState(false);
  const [agentInputs, setAgentInputs] = useState<Record<string, string | string[]>>({});
  const [copyState, setCopyState] = useState<"idle" | "copied">("idle");
  const [exportState, setExportState] = useState<"idle" | "exporting">("idle");

  const statusIntervalRef = useRef<number | null>(null);
  const revealTimersRef = useRef<number[]>([]);

  useEffect(() => {
    const myBrandId = localStorage.getItem(MY_BRAND_WORKSPACE_KEY) || "";
    setMyBrandWorkspaceId(myBrandId);
    
    apiGet<WorkspaceSummary[]>("/workspaces")
      .then((rows) => {
        console.log("Fetched workspaces:", rows);
        setWorkspaces(rows);
        if (myBrandId && rows.some(w => w.workspace_id === myBrandId)) {
          setWorkspaceId(myBrandId);
        } else if (rows[0]) {
          setWorkspaceId(rows[0].workspace_id);
        }
      })
      .catch(() => setWorkspaces([]));
    if (agentId) {
      apiGet<AgentSpec>(`/agents/${agentId}`).then(setSpec).catch(() => setSpec(null));
    }
  }, [agentId]);

  useEffect(() => {
    setBrandName("");
    setBrandContext("");
    setAdditionalDetails("");
    setCompetitors("");
    setQueries("");
    setCategoryKeywords("");
    setTimeWindow("Last 90 days");
    setPrimaryConcern("All");
    setGoal("All");
    setActiveStep(1);
    setRunState("idle");
    setRevealedCount(0);
    setSavedState("idle");
    setBrandEquityReportData(null); // Reset report data on agent change
    // Reset local UI specific state to ensure isolation between agent types
    setCollapsed({});
    setErrors({});
    setIncludedIntegrations((prev) => {
      const reset = { ...prev };
      return reset;
    });
  }, [agentId]);

  useEffect(() => {
    if (!workspaceId || workspaceId === "__new__") return;
    apiGet<IntegrationState[]>(`/integrations/${workspaceId}`)
      .then((rows) => {
        const byProvider = rows.reduce<Record<string, IntegrationState>>((acc, row) => ({ ...acc, [row.provider]: row }), {});
        setIntegrations(byProvider);
        setIncludedIntegrations((prev) => {
          const next = { ...prev };
          PROVIDERS.forEach((p) => {
            if (next[p.id] === undefined) next[p.id] = Boolean(byProvider[p.id]?.connected);
          });
          return next;
        });
      })
      .catch(() => setIntegrations({}));
  }, [workspaceId]);

  useEffect(() => {
    return () => {
      if (statusIntervalRef.current) window.clearInterval(statusIntervalRef.current);
      revealTimersRef.current.forEach((t) => window.clearTimeout(t));
    };
  }, []);

  const selectedWorkspace = useMemo(() => workspaces.find((w) => w.workspace_id === workspaceId) || null, [workspaceId, workspaces]);
  const workspaceMemoryCount = selectedWorkspace?.brand_analysis
    ? Object.keys(selectedWorkspace.brand_analysis).length
    : 0;

  useEffect(() => {
    if (!autoAddContext || !selectedWorkspace) return;
    const context = [
      selectedWorkspace.brand_summary,
      selectedWorkspace.positioning,
      selectedWorkspace.additional_details,
    ]
      .filter(Boolean)
      .join("\n");
    if (context.trim()) {
      setBrandContext(context);
      setBrandName((prev) => prev || selectedWorkspace.brand_name || prev);
    }
  }, [autoAddContext, selectedWorkspace]);

  const brandContextCount = brandContext.length;

  function validateAgentInputs(): string | undefined {
    const agentInputsConfig = getAgentInputs(agentId);
    for (const input of agentInputsConfig) {
      if (input.required) {
        const value = agentInputs[input.key];
        if (input.type === "multiselect") {
          if (!value || (Array.isArray(value) && value.length === 0)) {
            return `${input.label} is required`;
          }
        } else {
          if (!value || (typeof value === "string" && !value.trim())) {
            return `${input.label} is required`;
          }
        }
      }
    }
    return undefined;
  }

  function validateField(key: keyof FieldErrors): string | undefined {
    if (key === "brandName" && !brandName.trim()) return "This field is required";
    if (key === "brandContext" && !brandContext.trim()) return "This field is required";
    return undefined;
  }

  function onBlurField(key: keyof FieldErrors) {
    setErrors((prev) => ({ ...prev, [key]: validateField(key) }));
  }

  function validateAll(): boolean {
    const next: FieldErrors = {
      brandName: validateField("brandName"),
      brandContext: validateField("brandContext"),
    };
    setErrors(next);
    if (Object.values(next).some(Boolean)) return false;
    const agentError = validateAgentInputs();
    if (agentError) {
      setErrors({ brandName: agentError });
      return false;
    }
    return true;
  }

  async function toggleIntegration(provider: string, enabled: boolean) {
    if (!workspaceId || workspaceId === "__new__") return;
    
    const currentIntegration = integrations[provider];
    const isOAuthProvider = provider === "ga4" || provider === "gsc";
    
    if (enabled && isOAuthProvider) {
      try {
        const authResponse = await apiGet<{ auth_url: string; redirect_uri: string; provider: string }>(`/integrations/auth-url/${provider}`);
        
        if (authResponse.auth_url) {
          const popup = window.open(authResponse.auth_url, "_blank", "width=600,height=700,scrollbars=yes");
          
          if (!popup) {
            await showAlert("Popup Blocked", "Please allow popups and try again, or click the Connect button directly.");
            return;
          }
          
          const pollTimer = window.setInterval(async () => {
            try {
              if (popup.closed) {
                window.clearInterval(pollTimer);
                const rows = await apiGet<IntegrationState[]>(`/integrations/${workspaceId}`);
                const byProvider = rows.reduce<Record<string, IntegrationState>>((acc, row) => ({ ...acc, [row.provider]: row }), {});
                setIntegrations(byProvider);
                setIncludedIntegrations((prev) => ({ ...prev, [provider]: true }));
              }
            } catch (e) {
              console.log("Waiting for OAuth callback...");
            }
          }, 1000);
          
          return;
        }
      } catch (err) {
        console.error("Failed to start OAuth flow:", err);
        await showAlert("Connection Failed", `Failed to connect ${provider}: ${err instanceof Error ? err.message : String(err)}`);
        return;
      }
    }
    
    if (!enabled && isOAuthProvider) {
      try {
        const statusResponse = await apiGet<{ connected: boolean; message: string }>(`/integrations/status/${provider}`);
        if (statusResponse.connected) {
          await apiPost("/integrations/connect", {
            workspace_id: workspaceId,
            provider,
            enabled: false,
            scopes: [],
            auth_metadata: {},
          });
        }
      } catch (err) {
        console.error("Failed to disconnect:", err);
      }
    } else {
      await apiPost("/integrations/connect", {
        workspace_id: workspaceId,
        provider,
        enabled,
        scopes: enabled ? ["read"] : [],
        auth_metadata: enabled ? { mode: "scaffold" } : {},
      });
    }
    
    const rows = await apiGet<IntegrationState[]>(`/integrations/${workspaceId}`);
    const byProvider = rows.reduce<Record<string, IntegrationState>>((acc, row) => ({ ...acc, [row.provider]: row }), {});
    setIntegrations(byProvider);
    setIncludedIntegrations((prev) => ({ ...prev, [provider]: enabled }));
  }

  function autoFillFromWorkspace() {
    if (!selectedWorkspace) return;
    setIsAutoFilling(true);
    window.setTimeout(() => {
      setBrandName(selectedWorkspace.brand_name || brandName);
      const context = [selectedWorkspace.brand_summary, selectedWorkspace.positioning, selectedWorkspace.additional_details].filter(Boolean).join("\n");
      if (context.trim()) setBrandContext(context);
      
      const agentConfig = AGENT_INPUT_CONFIGS[agentId];
      if (agentConfig?.workspace_mapping) {
        const newAgentInputs: Record<string, string | string[]> = { ...agentInputs };
        Object.entries(agentConfig.workspace_mapping).forEach(([inputKey, workspaceField]) => {
          const workspaceValue = (selectedWorkspace as any)[workspaceField];
          if (workspaceValue !== undefined && workspaceValue !== null && workspaceValue !== "") {
            newAgentInputs[inputKey] = workspaceValue;
          }
        });
        setAgentInputs(newAgentInputs);
      }
      
      setIsAutoFilling(false);
    }, 700);
  }

  async function onRun() {
    const { allowed, reason } = canRun();
    if (!allowed) {
      if (reason === "signup") {
        await showAlert("Runs Exhausted", "You've used all 5 free runs. Sign up to get 20 more free runs!");
        window.location.href = "/auth-account-system.html#/signup";
      } else if (reason === "upgrade") {
        await showAlert("Runs Exhausted", "You've used all 25 free runs. Upgrade to a paid plan for unlimited access!");
      }
      return;
    }

    if (!validateAll()) {
      setActiveStep(3);
      return;
    }
    setActiveStep(4);

    if (statusIntervalRef.current) window.clearInterval(statusIntervalRef.current);
    revealTimersRef.current.forEach((t) => window.clearTimeout(t));
    revealTimersRef.current = [];

    setRunState("loading");
    setRevealedCount(0);
    setStatusIdx(0);
    setBrandEquityReportData(null);

    const agentProgressMessages = AGENT_INPUT_CONFIGS[agentId]?.progress_messages || STATUS_MESSAGES;
    statusIntervalRef.current = window.setInterval(() => {
      setStatusIdx((prev) => (prev + 1) % agentProgressMessages.length);
    }, 4000);

    try {
      // Build input payload from agentInputs
      const inputPayload: Record<string, any> = {
        brand_name: brandName,
        brand_context: brandContext,
      };
      
      // Add all agent-specific inputs
      const inputsConfig = getAgentInputs(agentId);
      for (const input of inputsConfig) {
        const value = agentInputs[input.key];
        if (value !== undefined && value !== null && value !== "") {
          // Convert textarea values (comma or newline separated) to arrays
          if (input.type === "textarea" && typeof value === "string") {
            const splitValue = value.includes("\n") 
              ? value.split("\n").map(s => s.trim()).filter(Boolean)
              : value.includes(",") 
                ? value.split(",").map(s => s.trim()).filter(Boolean)
                : value;
            inputPayload[input.key] = splitValue;
          } else if (input.type === "multiselect" && Array.isArray(value)) {
            inputPayload[input.key] = value;
          } else {
            inputPayload[input.key] = value;
          }
        }
      }
      
      const response = await apiPost<any>(`/agents/run`, {
        agent_id: agentId,
        workspace_id: workspaceId,
        input_payload: inputPayload,
      });

      // response from backend is the 'output' dict from executor
      // Handle different agent output formats - data is nested in output
      console.log("API Response keys:", response ? Object.keys(response) : "null");
      const output = response?.output || response;
      console.log("Output keys:", output ? Object.keys(output) : "null");
      const reportData = isBrandEquity 
        ? output?.brand_equity_data 
        : (output?.result || output?.dashboard || output?.content_pack || output);
      console.log("ReportData:", reportData);
      console.log("ReportData type:", typeof reportData);

      // Extract debug info from backend
      if (output?._debug) {
        setDebugInfo({
          source: output._debug.source || "unknown",
          missing_fields: output._debug.missing_sections || output._debug.missing_fields || [],
          llm_returned: output._debug.llm_raw || output._debug.llm_returned || null,
          filled_sections: output._debug.filled_sections || [],
          error: output._debug.error || null,
        });
      }

      setBrandEquityReportData(reportData);
      setRunState("complete");
      
      incrementRuns(agentId as string);

      if (statusIntervalRef.current) window.clearInterval(statusIntervalRef.current);
      
      // Count sections for reveal animation
      const sectionsCount = isBrandEquity ? activeSectionKeys.length : (reportData ? Object.keys(reportData).filter(k => !['sections', 'executive_summary', 'summary', 'title', 'agent_title', 'report_title', 'generated_at', 'input_echo'].includes(k)).length : 0);
      console.log("Sections to render:", sectionsCount);
      for (let i = 0; i < sectionsCount; i++) {
        const timer = window.setTimeout(() => setRevealedCount(i + 1), 400 * (i + 1));
        revealTimersRef.current.push(timer);
      }
    } catch (err) {
      console.error("Agent run failed:", err);
      setRunState("idle");
      if (statusIntervalRef.current) window.clearInterval(statusIntervalRef.current);
    }
  }

  function saveToWorkspace() {
    if (!brandEquityReportData) return;
    setSavedState("saving");
    
    try {
      const runId = `run_${Date.now()}`;
      const reportToSave = {
        run_id: runId,
        agent_id: agentId,
        agent_name: spec?.name || agentId,
        workspace_id: workspaceId || "local",
        brand_name: brandName,
        report: brandEquityReportData,
        saved_at: new Date().toISOString(),
      };
      
      const historyKey = `marketing_agents_report_history_${workspaceId || "local"}`;
      const existingHistory = JSON.parse(localStorage.getItem(historyKey) || "[]");
      existingHistory.unshift(reportToSave);
      localStorage.setItem(historyKey, JSON.stringify(existingHistory.slice(0, 50)));
      
      setSavedState("saved");
      window.setTimeout(() => setSavedState("idle"), 2000);
    } catch (err) {
      console.error("Failed to save report:", err);
      setSavedState("idle");
    }
  }

  function copyReport() {
    if (!brandEquityReportData) return;
    setCopyState("copied");
    
    const title = brandEquityReportData?.title || brandEquityReportData?.agent_title || "Agent Analysis Report";
    const summary = brandEquityReportData?.executive_summary || brandEquityReportData?.summary || "";
    
    let reportText = `${title}\n${"=".repeat(title.length)}\n\n`;
    reportText += summary ? `${summary}\n\n` : "";
    
    const sections = brandEquityReportData?.sections || [];
    if (sections.length > 0) {
      sections.forEach((section: any) => {
        const sectionTitle = section.title || section.key || "Section";
        reportText += `${sectionTitle}\n${"-".repeat(sectionTitle.length)}\n`;
        if (typeof section.content === 'string') {
          reportText += `${section.content}\n\n`;
        } else if (Array.isArray(section.content)) {
          section.content.forEach((item: any) => {
            reportText += `• ${typeof item === 'string' ? item : JSON.stringify(item, null, 2)}\n`;
          });
          reportText += "\n";
        }
      });
    } else {
      Object.entries(brandEquityReportData).forEach(([key, value]) => {
        if (!['sections', 'executive_summary', 'summary', 'title', 'agent_title', 'report_title', 'generated_at', 'input_echo'].includes(key) && value !== null && value !== undefined) {
          const keyTitle = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
          reportText += `${keyTitle}\n${"-".repeat(keyTitle.length)}\n`;
          if (typeof value === 'string') {
            reportText += `${value}\n\n`;
          } else if (Array.isArray(value)) {
            value.forEach((item) => {
              reportText += `• ${typeof item === 'string' ? item : JSON.stringify(item, null, 2)}\n`;
            });
            reportText += "\n";
          } else if (typeof value === 'object') {
            reportText += `${JSON.stringify(value, null, 2)}\n\n`;
          }
        }
      });
    }
    
    reportText += `\n---\nGenerated by MarketingAgents.ai | ${new Date().toLocaleString()}`;
    
    navigator.clipboard.writeText(reportText).then(() => {
      window.setTimeout(() => setCopyState("idle"), 2000);
    }).catch(err => {
      console.error("Failed to copy:", err);
      setCopyState("idle");
    });
  }

  async function exportPDF() {
    if (!brandEquityReportData) return;
    setExportState("exporting");
    
    const title = brandEquityReportData?.title || brandEquityReportData?.agent_title || "Agent Analysis Report";
    const summary = brandEquityReportData?.executive_summary || brandEquityReportData?.summary || "";
    
    let reportHTML = `
      <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 40px 20px; color: #1a1a2e;">
        <div style="text-align: center; margin-bottom: 40px; border-bottom: 3px solid #4f6ef7; padding-bottom: 20px;">
          <h1 style="margin: 0 0 10px; color: #4f6ef7; font-size: 28px;">${title}</h1>
          <p style="margin: 0; color: #6b7280; font-size: 14px;">Generated by MarketingAgents.ai</p>
          <p style="margin: 10px 0 0; color: #6b7280; font-size: 12px;">${new Date().toLocaleString()}</p>
        </div>
        ${summary ? `<div style="background: #f3f4f6; border-left: 4px solid #4f6ef7; padding: 16px; margin-bottom: 30px; border-radius: 8px;"><p style="margin: 0; color: #374151; line-height: 1.6;">${summary}</p></div>` : ''}
    `;
    
    const sections = brandEquityReportData?.sections || [];
    if (sections.length > 0) {
      sections.forEach((section: any, idx: number) => {
        const sectionTitle = section.title || section.key || "Section";
        const colors = ['#4f6ef7', '#00b894', '#8b5cf6', '#f59e0b', '#ec4899', '#06b6d4'];
        const color = colors[idx % colors.length];
        reportHTML += `
          <div style="margin-bottom: 24px; page-break-inside: avoid;">
            <h2 style="color: ${color}; font-size: 18px; margin: 0 0 12px; padding-bottom: 8px; border-bottom: 2px solid ${color}20;">${sectionTitle}</h2>
            <div style="color: #374151; line-height: 1.7; font-size: 14px;">
              ${typeof section.content === 'string' ? section.content.replace(/\n/g, '<br>') : formatContentForPDF(section.content)}
            </div>
          </div>
        `;
      });
    } else {
      Object.entries(brandEquityReportData).forEach(([key, value], idx) => {
        if (!['sections', 'executive_summary', 'summary', 'title', 'agent_title', 'report_title', 'generated_at', 'input_echo'].includes(key) && value !== null && value !== undefined) {
          const keyTitle = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
          const colors = ['#4f6ef7', '#00b894', '#8b5cf6', '#f59e0b', '#ec4899', '#06b6d4'];
          const color = colors[idx % colors.length];
          reportHTML += `
            <div style="margin-bottom: 20px; page-break-inside: avoid;">
              <h3 style="color: ${color}; font-size: 16px; margin: 0 0 8px; padding-bottom: 6px; border-bottom: 1px solid #e5e7eb;">${keyTitle}</h3>
              <div style="color: #374151; line-height: 1.6; font-size: 13px;">
                ${formatValueForPDF(value)}
              </div>
            </div>
          `;
        }
      });
    }
    
    // Add brand summary to PDF
    if (selectedWorkspace) {
      const brandFields = [
        { label: 'Brand Name', value: selectedWorkspace.brand_name },
        { label: 'Industry', value: selectedWorkspace.industry },
        { label: 'Category', value: selectedWorkspace.category },
        { label: 'Geography', value: selectedWorkspace.geography },
        { label: 'Website', value: selectedWorkspace.website },
        { label: 'Company', value: selectedWorkspace.workspace_name },
      ].filter(f => f.value);
      
      if (brandFields.length > 0) {
        reportHTML += `
          <div style="margin-top: 30px; page-break-before: auto;">
            <h3 style="color: #6b7280; font-size: 14px; margin: 0 0 16px; padding-bottom: 8px; border-bottom: 1px solid #e5e7eb; text-transform: uppercase; letter-spacing: 0.05em;">Brand Summary</h3>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px;">
              ${brandFields.map(f => `
                <div style="background: #f9fafb; padding: 12px; border-radius: 6px;">
                  <div style="font-size: 11px; color: #9ca3af; text-transform: uppercase; margin-bottom: 4px;">${f.label}</div>
                  <div style="font-size: 14px; color: #374151; font-weight: 500;">${f.value}</div>
                </div>
              `).join('')}
            </div>
            ${selectedWorkspace.positioning ? `
              <div style="background: #f9fafb; padding: 16px; border-radius: 8px; margin-top: 12px;">
                <div style="font-size: 11px; color: #9ca3af; text-transform: uppercase; margin-bottom: 8px;">Positioning</div>
                <div style="font-size: 13px; color: #374151; line-height: 1.5;">${selectedWorkspace.positioning.replace(/\n/g, '<br>')}</div>
              </div>
            ` : ''}
            ${selectedWorkspace.brand_summary ? `
              <div style="background: #f9fafb; padding: 16px; border-radius: 8px; margin-top: 12px;">
                <div style="font-size: 11px; color: #9ca3af; text-transform: uppercase; margin-bottom: 8px;">Brand Summary</div>
                <div style="font-size: 13px; color: #374151; line-height: 1.5;">${selectedWorkspace.brand_summary.replace(/\n/g, '<br>')}</div>
              </div>
            ` : ''}
          </div>
        `;
      }
    }
    
    reportHTML += `
      <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; text-align: center; color: #9ca3af; font-size: 11px;">
        <p>Generated by MarketingAgents.ai | ${new Date().toLocaleString()}</p>
      </div>
      <style>
        @media print {
          body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
        }
      </style>
    `;
    
    const printWindow = window.open('', '_blank');
    if (printWindow) {
      printWindow.document.write(`
        <!DOCTYPE html>
        <html>
          <head>
            <title>${title}</title>
            <meta charset="UTF-8">
          </head>
          <body>${reportHTML}</body>
        </html>
      `);
      printWindow.document.close();
      printWindow.focus();
      setTimeout(() => {
        printWindow.print();
        setExportState("idle");
      }, 500);
    } else {
      await showAlert("Popup Blocked", "Please allow popups to export PDF");
      setExportState("idle");
    }
  }

  function formatContentForPDF(content: any): string {
    if (!content) return '';
    if (typeof content === 'string') return content.replace(/\n/g, '<br>');
    if (Array.isArray(content)) {
      return content.map(item => {
        if (typeof item === 'string') return `<span style="display: block; margin: 4px 0;">• ${item}</span>`;
        if (typeof item === 'object') return `<span style="display: block; margin: 4px 0;">• ${JSON.stringify(item, null, 2).replace(/\n/g, '<br>')}</span>`;
        return '';
      }).join('');
    }
    return String(content);
  }

  function formatValueForPDF(value: any): string {
    if (typeof value === 'string') return value.replace(/\n/g, '<br>');
    if (typeof value === 'number') return `<strong>${value}</strong>`;
    if (value === null || value === undefined) return '<em>No data</em>';
    if (Array.isArray(value)) {
      if (value.length === 0) return '<em>No items</em>';
      return value.map(item => {
        if (typeof item === 'string') return `<span style="display: block; margin: 4px 0;">• ${item}</span>`;
        if (typeof item === 'object' && item !== null) {
          const entries = Object.entries(item).map(([k, v]) => {
            const label = k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
            const displayValue = typeof v === 'object' ? JSON.stringify(v) : v;
            return `<span style="display: block; margin: 2px 0; padding-left: 12px;"><strong>${label}:</strong> ${displayValue}</span>`;
          }).join('');
          return `<span style="display: block; margin: 4px 0; padding: 8px; background: #f9fafb; border-radius: 4px;">${entries || '• (object)'}</span>`;
        }
        return `<span style="display: block; margin: 4px 0;">• ${String(item)}</span>`;
      }).join('');
    }
    if (typeof value === 'object') {
      return Object.entries(value).map(([k, v]) => {
        const label = k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
        if (typeof v === 'object') {
          return `<div style="margin: 8px 0;"><strong>${label}:</strong><div style="margin-left: 12px; padding: 4px; background: #f9fafb; border-radius: 4px;">${formatValueForPDF(v)}</div></div>`;
        }
        return `<div style="margin: 4px 0;"><strong>${label}:</strong> ${v}</div>`;
      }).join('');
    }
    return String(value);
  }

  function toggleSection(key: string) {
    setCollapsed((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  function renderFieldValue(value: any): JSX.Element {
    if (value === null || value === undefined) {
      return <p className="no-signal">No data available</p>;
    }
    
    if (typeof value === 'string') {
      return <p className="whitespace-pre-wrap">{value}</p>;
    }
    
    if (typeof value === 'number') {
      return <p className="score-display"><strong>{value}</strong></p>;
    }
    
    if (Array.isArray(value)) {
      if (value.length === 0) {
        return <p className="no-signal">No items</p>;
      }
      return (
        <ul className="result-list">
          {value.map((item, i) => (
            <li key={i} className="result-list-item">
              {typeof item === 'object' ? renderFieldValue(item) : (
                <span>{typeof item === 'string' ? item : JSON.stringify(item)}</span>
              )}
            </li>
          ))}
        </ul>
      );
    }
    
    if (typeof value === 'object') {
      return (
        <div className="result-object">
          {Object.entries(value).map(([k, v]) => (
            <div key={k} className="result-field">
              <strong className="field-label">{k.replace(/_/g, ' ')}</strong>
              <div className="field-value">{renderFieldValue(v)}</div>
            </div>
          ))}
        </div>
      );
    }
    
    return <p>{String(value)}</p>;
  }

  const isBrandEquity = agentId === "brand_equity_tracker_agent";
  const activeSectionKeys = isBrandEquity ? BRAND_EQUITY_SECTION_KEYS : GENERAL_SECTION_KEYS;
  const runtimeLabel = "~3 min run time";
  const categoryLabel = spec?.category || (isBrandEquity ? "Brand Strategy & Health" : "Channel & Visibility"); // Keep this
  const nameLabel = spec?.name || "Brand Equity Tracker Agent"; // Keep this
  const iconLabel = AGENT_ICON[agentId] || "📈"; // Keep this
  const descriptionLabel = spec?.description || spec?.summary || (isBrandEquity ? "Aggregate public signals into a CMO-ready brand health report." : "Run this agent with your brand context to generate marketer-ready recommendations in minutes."); // Keep this

  const generalSkeletons = [
    "AI Share of Voice",
    "Visibility by Query",
    "Representation Accuracy",
    "AI Sentiment",
  ];

  const brandEquitySectionRenderers: {
    key: SectionKey;
    title: string;
    subtitle: string;
    render: () => JSX.Element;
  }[] = [
    {
      key: "brand_health_score",
      title: "Brand Health Score",
      subtitle: "Overall pulse a CMO can quote",
      render: () => {
        const data = brandEquityReportData?.brand_health_score;
        return (
          <div className="brand-health-score">
            <div className="health-score-value">
              <strong>{data?.overall_score || "--"}</strong>
              <span>/100</span>
            </div>
            <p className="rating-line">
              Rating: <strong>{data?.rating || "Pending"}</strong>
            </p>
            <p className="verdict-line">{data?.verdict || "Analyzing signals..."}</p>
            <div className="health-dimensions">
              {(data?.dimensions || []).map((dimension: any) => (
                <div key={dimension.label} className="dimension-row">
                  <span className="dimension-label">{dimension.label}</span>
                  <div className="dimension-bar">
                    <div style={{ width: `${(dimension.score / 20) * 100}%` }} />
                  </div>
                  <em className="dimension-score">{dimension.score}/20</em>
                </div>
              ))}
            </div>
          </div>
        );
      },
    },
    {
      key: "pulse_summary",
      title: "Pulse Summary",
      subtitle: "Key signals at a glance",
      render: () => (
        <div className="pulse-summary">
          <p className="pulse-intro">One finding per dimension:</p>
          <ul className="pulse-bullets">
            {(brandEquityReportData?.pulse_summary || []).map((bullet: string, idx: number) => (
              <li key={idx}>{bullet}</li>
            ))}
            {(!brandEquityReportData?.pulse_summary || brandEquityReportData.pulse_summary.length === 0) && (
              <li>No clear signal in {timeWindow}</li>
            )}
          </ul>
        </div>
      ),
    },
    {
      key: "biggest_risk",
      title: "Biggest Risk Right Now",
      subtitle: "One priority threat",
      render: () => {
        const data = brandEquityReportData?.biggest_risk;
        if (!data || (!data.what && !data.evidence)) {
          return <p className="no-signal">No clear signal in {timeWindow}</p>;
        }
        return (
          <div className="risk-detail">
            <div className="risk-what">
              <strong>What:</strong> {data.what}
            </div>
            <div className="risk-evidence">
              <strong>Evidence:</strong> {data.evidence}
            </div>
            <div className="risk-severity">
              <strong>Severity:</strong> 
              <span className={`severity-badge severity-${(data.severity || "medium").toLowerCase()}`}>
                {data.severity}
              </span>
            </div>
            <div className="risk-action">
              <strong>Action:</strong> {data.action}
            </div>
          </div>
        );
      },
    },
    {
      key: "biggest_opportunity",
      title: "Biggest Opportunity Right Now",
      subtitle: "One priority move",
      render: () => {
        const data = brandEquityReportData?.biggest_opportunity;
        if (!data || (!data.what && !data.why_now)) {
          return <p className="no-signal">No clear signal in {timeWindow}</p>;
        }
        return (
          <div className="opportunity-detail">
            <div className="opp-what">
              <strong>What:</strong> {data.what}
            </div>
            <div className="opp-why">
              <strong>Why now:</strong> {data.why_now}
            </div>
            <div className="opp-action">
              <strong>Action:</strong> {data.action}
            </div>
          </div>
        );
      },
    },
    {
      key: "ai_visibility_snapshot",
      title: "AI Visibility Snapshot",
      subtitle: "How AI platforms represent the brand",
      render: () => {
        const data = brandEquityReportData?.ai_visibility_snapshot;
        if (!data) {
          return <p className="no-signal">No clear signal in {timeWindow}</p>;
        }
        return (
          <div className="ai-visibility-snapshot">
            <div className="ai-status">
              <strong>Status:</strong>
              <span className={`status-badge status-${(data.status || "partial").toLowerCase()}`}>
                {data.status || "Unknown"}
              </span>
            </div>
            <div className="ai-context">
              <strong>Context:</strong> {data.context_line || "No clear signal"}
            </div>
            <div className="ai-competitor">
              <strong>vs. Competitors:</strong> {data.leader_vs_competitors || "Unable to determine"}
            </div>
          </div>
        );
      },
    },
    {
      key: "brand_associations",
      title: "Brand Associations",
      subtitle: "What the brand owns in perception",
      render: () => {
        const data = brandEquityReportData?.brand_associations;
        return (
          <div className="brand-associations">
            <div className="assoc-owned">
              <strong>Owned:</strong>
              <p className="assoc-words">{(data?.owned || []).join(" · ") || "No clear signal"}</p>
            </div>
            <div className="assoc-intended">
              <strong>Intended:</strong>
              <p className="assoc-words">{(data?.intended || []).join(" · ") || "None specified"}</p>
            </div>
            <div className="assoc-gap">
              <strong>Gap:</strong>
              <p>{data?.gap_line || "No significant gap detected"}</p>
            </div>
          </div>
        );
      },
    },
    {
      key: "top_3_actions",
      title: "Top 3 Actions",
      subtitle: "Prioritised by urgency",
      render: () => (
        <div className="top-actions">
          <ol className="action-list">
            {(brandEquityReportData?.top_3_actions || []).map((action: string, idx: number) => (
              <li key={idx} className="action-item">{action}</li>
            ))}
            {(!brandEquityReportData?.top_3_actions || brandEquityReportData.top_3_actions.length === 0) && (
              <li>No actions generated yet</li>
            )}
          </ol>
        </div>
      ),
    },
  ];
  // End of brandEquitySectionRenderers

  return (
    <div className="agent-run-page grid">
      <Link href={"/agents" as Route} className="agent-run-back">← Agent Studio</Link>

      <section className="agent-run-head">
        <div className="agent-run-identity">
          <div className="agent-run-icon">{iconLabel}</div>
          <div>
            <h1>{nameLabel}</h1>
            <span className="agent-run-category-pill">{categoryLabel}</span>
            <p>{descriptionLabel}</p>
          </div>
        </div>
        <div className="agent-run-meta-pills">
          <span>⏱ {runtimeLabel}</span>
          <span>🔍 Web search enabled</span>
          <span>📋 Workspace ready</span>
        </div>
      </section>

      <section className="agent-run-layout">
        <aside className={`agent-run-left ${runState === "loading" ? "is-loading" : ""}`}>
          <div className="agent-run-left-head">
            <h3>Configure Your Run</h3>
            <p>
              Fill in the details below to generate your {isBrandEquity ? "brand health report" : "AI visibility report"}.
            </p>
          </div>

          <section className="agent-step">
            <button className="agent-step-head" onClick={() => setActiveStep(1)}>
              <span className={`agent-step-no ${activeStep >= 1 ? "active" : ""}`}>1</span>
              <div>
                <strong>Brand Workspace</strong>
                <small>Load your brand context automatically from a saved workspace — or enter it manually below.</small>
              </div>
            </button>
            <div className={`agent-step-body ${activeStep === 1 ? "open" : ""}`}>
              <label>Brand Workspace</label>
              <select className="select" value={workspaceId} onChange={(e) => setWorkspaceId(e.target.value)}>
                <option value="">Select a workspace...</option>
                {myBrandWorkspaceId && workspaces.some(w => w.workspace_id === myBrandWorkspaceId) && (
                  <option value={myBrandWorkspaceId} disabled>★ My Brand Workspace</option>
                )}
                {myBrandWorkspaceId && (
                  <option value={myBrandWorkspaceId}>  ★ My Brand — {workspaces.find(w => w.workspace_id === myBrandWorkspaceId)?.brand_name || myBrandWorkspaceId}</option>
                )}
                {myBrandWorkspaceId && <option value="" disabled>— Other Workspaces —</option>}
                {workspaces.filter(w => w.workspace_id !== myBrandWorkspaceId).map((w) => (
                  <option key={w.workspace_id} value={w.workspace_id}>{w.workspace_name} — {w.brand_name}</option>
                ))}
                <option value="__new__">+ Add New Workspace</option>
              </select>

              {workspaces.length === 0 && workspaceId === "" && (
                <p className="text-sm text-gray-500 mt-2">
                  No workspaces found. Please create one using the link below, or ensure your backend server is running and accessible.
                </p>
              )}

              {workspaceId === "__new__" ? (
                <Link className="agent-inline-link" href={`/workspaces?next=/run/${agentId}` as Route}>Create in Brand Workspace →</Link>
              ) : null}

              {selectedWorkspace ? (
                <div className="agent-workspace-loaded">
                  <p>✓ Workspace loaded</p>
                  <strong>{selectedWorkspace.brand_name}</strong>
                  <span>Brand context auto-filled below ↓</span>
                  <Link href={"/workspaces" as Route}>View workspace →</Link>
                  {selectedWorkspace.workspace_id !== myBrandWorkspaceId ? (
                    <button 
                      className="agent-set-my-brand-btn"
                      onClick={() => {
                        localStorage.setItem(MY_BRAND_WORKSPACE_KEY, selectedWorkspace.workspace_id);
                        setMyBrandWorkspaceId(selectedWorkspace.workspace_id);
                      }}
                    >
                      ★ Set as My Brand Workspace
                    </button>
                  ) : (
                    <span className="agent-my-brand-indicator">★ My Brand Workspace</span>
                  )}
                </div>
              ) : null}

              <label className="agent-checkbox-row">
                <input type="checkbox" checked={autoAddContext} onChange={(e) => setAutoAddContext(e.target.checked)} />
                Add workspace context automatically
              </label>

              <div className="agent-memory-row">
                <span>📄 {workspaceMemoryCount} document{workspaceMemoryCount === 1 ? "" : "s"} in workspace memory</span>
                <a href="#">Learn about workspace memory →</a>
              </div>

              <button className="agent-autofill-btn" onClick={autoFillFromWorkspace}>
                ✨ {isAutoFilling ? "Auto-filling..." : "Auto-fill brand context from workspace"}
              </button>
            </div>
          </section>

          <section className="agent-step">
            <button className="agent-step-head" onClick={() => setActiveStep(2)}>
              <span className={`agent-step-no ${activeStep >= 2 ? "active" : ""}`}>2</span>
              <div>
                <strong>Enhance with Data</strong>
                <small>Connect marketing tools to enrich agent output with your real performance data.</small>
              </div>
            </button>
            <div className={`agent-step-body ${activeStep === 2 ? "open" : ""}`}>
              <div className="agent-integrations-row">
                {PROVIDERS.map((provider) => {
                  const row = integrations[provider.id];
                  const connected = Boolean(row?.connected);
                  const include = Boolean(includedIntegrations[provider.id]);
                  return (
                    <article key={provider.id} className="agent-integration-card">
                      <div className="agent-integration-logo">{provider.icon}</div>
                      <strong>{provider.label}</strong>
                      <small>{provider.value}</small>
                      <div className="agent-integration-status">
                        <i className={connected ? "on" : "off"} />
                        <span>{connected ? "Connected" : "Not connected"}</span>
                      </div>
                      <label className="agent-checkbox-row">
                        <input
                          type="checkbox"
                          checked={include}
                          onChange={(e) => setIncludedIntegrations((prev) => ({ ...prev, [provider.id]: e.target.checked }))}
                        />
                        Include in this run
                      </label>
                      <button
                        className={`btn ${connected ? "btn-subtle agent-disconnect" : "agent-connect"}`}
                        onClick={() => toggleIntegration(provider.id, !connected)}
                      >
                        {connected ? "Disconnect" : "Connect"}
                      </button>
                    </article>
                  );
                })}
              </div>
              <p className="agent-step-note">Agents run without integrations — connected tools add depth to your output.</p>
              <Link className="agent-inline-link" href={"/workspaces" as Route}>Set up integrations in Brand Workspace →</Link>
            </div>
          </section>

          <section className="agent-step">
            <button className="agent-step-head" onClick={() => setActiveStep(3)}>
              <span className={`agent-step-no ${activeStep >= 3 ? "active" : ""}`}>3</span>
              <div>
                <strong>Agent Inputs</strong>
                <small>Configure inputs specific to this agent.</small>
              </div>
            </button>
            <div className={`agent-step-body ${activeStep === 3 ? "open" : ""}`}>
              {/* Brand Name & Context - Standard for all agents */}
              <div className="agent-field">
                <label>Brand Name <span title="Required field">*</span></label>
                <input
                  className={`input ${errors.brandName ? "field-error shake" : ""}`}
                  value={brandName}
                  onChange={(e) => setBrandName(e.target.value)}
                  onBlur={() => onBlurField("brandName")}
                  placeholder="e.g. Maruti Suzuki Swift"
                />
                <small className={errors.brandName ? "error-text" : ""}>
                  {errors.brandName || "Your brand or product name."}
                </small>
              </div>
              <div className="agent-field">
                <label>Brand Context <span title="Required field">*</span></label>
                <textarea
                  className={`textarea ${errors.brandContext ? "field-error shake" : ""}`}
                  value={brandContext}
                  onChange={(e) => setBrandContext(e.target.value)}
                  onBlur={() => onBlurField("brandContext")}
                  placeholder="Summarize positioning, audiences, and what sets the brand apart."
                  maxLength={500}
                />
                <div className="agent-field-meta">
                  <small className={errors.brandContext ? "error-text" : ""}>
                    {errors.brandContext || "Auto-filled when you select a Brand Workspace."}
                  </small>
                  <span>{brandContextCount} / 500</span>
                </div>
              </div>

              {/* Dynamic Agent-Specific Inputs */}
              {getAgentInputs(agentId).map((input) => (
                <div key={input.key} className="agent-field">
                  <label>
                    {input.label}
                    {input.required && <span title="Required field"> *</span>}
                  </label>
                  
                  {input.type === "text" && (
                    <input
                      className="input"
                      value={(agentInputs[input.key] as string) || ""}
                      onChange={(e) => setAgentInputs((prev) => ({ ...prev, [input.key]: e.target.value }))}
                      placeholder={input.placeholder}
                    />
                  )}
                  
                  {input.type === "url" && (
                    <input
                      className="input"
                      type="url"
                      value={(agentInputs[input.key] as string) || ""}
                      onChange={(e) => setAgentInputs((prev) => ({ ...prev, [input.key]: e.target.value }))}
                      placeholder={input.placeholder}
                    />
                  )}
                  
                  {input.type === "textarea" && (
                    <textarea
                      className="textarea"
                      value={(agentInputs[input.key] as string) || ""}
                      onChange={(e) => setAgentInputs((prev) => ({ ...prev, [input.key]: e.target.value }))}
                      placeholder={input.placeholder}
                    />
                  )}
                  
                  {input.type === "dropdown" && (
                    <select
                      className="select"
                      value={(agentInputs[input.key] as string) || ""}
                      onChange={(e) => setAgentInputs((prev) => ({ ...prev, [input.key]: e.target.value }))}
                    >
                      <option value="">{input.placeholder || "Select..."}</option>
                      {input.options?.map((opt) => (
                        <option key={opt} value={opt}>{opt}</option>
                      ))}
                    </select>
                  )}
                  
                  {input.type === "multiselect" && (
                    <div className="agent-multiselect">
                      {input.multilineOptions?.map((opt) => (
                        <button
                          key={opt}
                          type="button"
                          className={`multiselect-btn ${((agentInputs[input.key] as string[]) || []).includes(opt) ? "active" : ""}`}
                          onClick={() => {
                            const current = (agentInputs[input.key] as string[]) || [];
                            const updated = current.includes(opt)
                              ? current.filter((o) => o !== opt)
                              : [...current, opt];
                            setAgentInputs((prev) => ({ ...prev, [input.key]: updated }));
                          }}
                        >
                          {opt}
                        </button>
                      ))}
                    </div>
                  )}
                  
                  <small>{input.helper}</small>
                </div>
              ))}
            </div>
          </section>

          <section className="agent-step">
            <button className="agent-step-head" onClick={() => setActiveStep(4)}>
              <span className={`agent-step-no ${activeStep >= 4 ? "active" : ""}`}>4</span>
              <div><strong>Generate Report</strong></div>
            </button>
            <div className={`agent-step-body ${activeStep === 4 ? "open" : ""}`}>
              <div className="agent-usage-banner">
                <div className="agent-usage-info">
                  <span className="agent-usage-icon">{getUserStatus().tier === "anonymous" ? "🎫" : "⭐"}</span>
                  <span className="agent-usage-text">
                    {getUserStatus().tier === "anonymous" 
                      ? `${getUserStatus().runs_remaining} of ${getUserStatus().runs_limit} free runs left`
                      : `${getUserStatus().runs_remaining} of ${getUserStatus().runs_limit} runs left`}
                  </span>
                </div>
                <div className="agent-usage-bar">
                  <div 
                    className="agent-usage-fill" 
                    style={{ width: `${Math.min(100, (getUserStatus().runs_used / getUserStatus().runs_limit) * 100)}%` }}
                  />
                </div>
              </div>
              
              {getUserStatus().is_blocked ? (
                <div className="agent-blocked-cta">
                  <div className="agent-blocked-message">
                    {getUserStatus().block_reason === "signup" ? (
                      <>
                        <h4>You&apos;ve used all 5 free runs!</h4>
                        <p>Sign up to get 20 more free runs and access your history across devices.</p>
                      </>
                    ) : (
                      <>
                        <h4>You&apos;ve used all 25 free runs!</h4>
                        <p>Upgrade to a paid plan for unlimited agent runs.</p>
                      </>
                    )}
                  </div>
                  <a 
                    href={getUserStatus().block_reason === "signup" 
                      ? "/auth-account-system.html#/signup" 
                      : "#"}
                    className="agent-run-btn-primary blocked"
                    onClick={getUserStatus().block_reason === "signup" ? undefined : (e) => { 
                      e.preventDefault(); 
                      showAlert("Coming Soon", "Paid plans coming soon! Contact us for early access."); 
                    }}
                  >
                    {getUserStatus().block_reason === "signup" 
                      ? "Sign Up for 20 More Free Runs" 
                      : "Upgrade to Pro"}
                  </a>
                </div>
              ) : (
                <>
                  <button className="agent-run-btn-primary" onClick={onRun}>
                    {runState === "loading" ? <span className="agent-spinner" /> : <span>✨</span>}
                    {runState === "loading"
                      ? "Analyzing..."
                      : isBrandEquity
                      ? "Generate Brand Health Report"
                      : "Generate AI Visibility Report"}
                  </button>
                  <p className="agent-run-footnote">~3 minutes · Powered by Claude AI + Web Search</p>
                  <p className="agent-run-footnote">🔒 Your data is never stored or used for training</p>
                </>
              )}
            </div>
          </section>
        </aside>

      <section className="agent-run-right">
        {runState === "idle" ? (
            <div className="agent-output-empty">
              <div className="agent-output-empty-icon">{iconLabel}</div>
              <h3>Your {isBrandEquity ? "brand health report" : "AI report"} will appear here</h3>
              <p>Configure your inputs on the left and run the agent to get a complete executive-ready analysis.</p>
              <div className="agent-output-skeletons">
                {isBrandEquity ? (
                  brandEquitySectionRenderers.map((item) => (
                    <div key={item.title}>
                      <small>{item.title}</small>
                    </div>
                  ))
                ) : (
                  (() => {
                    const expectedOutput = AGENT_INPUT_CONFIGS[agentId]?.expected_output || generalSkeletons;
                    return expectedOutput.map((title) => (
                      <div key={title}>
                        <small>{title}</small>
                      </div>
                    ));
                  })()
                )}
              </div>
            </div>
        ) : (
          <div className="agent-output-content">
            {runState === "loading" ? (
              <div className="agent-output-loading">
                <h4>Generating your report...</h4>
                <div className="agent-progress">
                  <span />
                </div>
                <p key={statusIdx}>{AGENT_INPUT_CONFIGS[agentId]?.progress_messages?.[statusIdx] || STATUS_MESSAGES[statusIdx]}</p>
              </div>
              ) : (
              <>
              <div className="agent-output-topbar">
                <div>
                  <h4>{brandEquityReportData?.title || brandEquityReportData?.agent_title || "Agent Analysis Report"}</h4>
                  <p>{brandEquityReportData?.executive_summary || brandEquityReportData?.summary || brandEquityReportData?.executive_summary_overall || `${brandName || "Brand"} · Generated just now`}</p>
                </div>
                <div className="agent-output-actions">
                  <button 
                    className="btn btn-subtle" 
                    onClick={exportPDF}
                    disabled={exportState === "exporting"}
                  >
                    {exportState === "exporting" ? "Exporting..." : "📄 Export PDF"}
                  </button>
                  <button 
                    className="btn btn-subtle" 
                    onClick={copyReport}
                    disabled={copyState === "copied"}
                  >
                    {copyState === "copied" ? "✓ Copied!" : "📋 Copy Report"}
                  </button>
                  <button 
                    className="btn" 
                    onClick={saveToWorkspace}
                    disabled={savedState === "saving"}
                  >
                    {savedState === "saved" ? "✓ Saved!" : savedState === "saving" ? "Saving..." : "💾 Save to Workspace"}
                  </button>
                </div>
              </div>

              </>
            )}

            <div className="agent-sections">
              {/* Brand Equity Tracker - use specific renderers */}
              {isBrandEquity && brandEquityReportData ? (
                brandEquitySectionRenderers.map((section, idx) =>
                  revealedCount >= idx + 1 ? (
                    <article key={section.key} className="agent-section-card stream-in">
                      <header>
                        <div>
                          <small>{section.title}</small>
                          <h5>{section.subtitle}</h5>
                        </div>
                        <button onClick={() => toggleSection(section.key)}>⌄</button>
                      </header>
                      {!collapsed[section.key] ? (
                        <div className="agent-section-body">{section.render()}</div>
                      ) : null}
                    </article>
                  ) : null
                )
              ) : (
                /* All other agents - use unified renderer */
                (() => {
                  if (!brandEquityReportData) {
                    return <p className="no-signal">Loading results...</p>;
                  }
                  
                  // Get all keys from the report data
                  const allKeys = Object.keys(brandEquityReportData).filter(k => 
                    !['sections', 'executive_summary', 'summary', 'title', 'agent_title', 'report_title', 'generated_at', 'input_echo'].includes(k)
                  );
                  
                  if (allKeys.length === 0) {
                    return <p className="no-signal">No analysis results available</p>;
                  }
                  
                  return allKeys.map((key, idx) => {
                    const value = brandEquityReportData[key];
                    if (value === null || value === undefined) return null;
                    
                    const title = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
                    
                    return revealedCount >= idx + 1 ? (
                      <article key={key} className="agent-section-card stream-in">
                        <header>
                          <div>
                            <small>{title}</small>
                            <h5>Analysis</h5>
                          </div>
                          <button onClick={() => toggleSection(key)}>⌄</button>
                        </header>
                        {!collapsed[key] ? (
                          <div className="agent-section-body">
                            {renderFieldValue(value)}
                          </div>
                        ) : null}
                      </article>
                    ) : null;
                  });
                })()
              )}
            </div>
          </div>
        )}
      </section>
    </section>
  </div>
  );
}
