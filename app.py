from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime
import logging
from pathlib import Path
from urllib.parse import quote
from urllib.parse import quote_plus
from urllib.parse import urlparse

import pandas as pd
import streamlit as st
from openai import OpenAI

from integrations.gsc_client import (
    authenticate_gsc,
    fetch_top_queries,
    get_gsc_status,
    list_gsc_properties,
)
from main import generate_query_set, run_competitor_intelligence, run_full_audit
from utils.config import settings
from utils.models import BrandContext, QueryItem
from utils.server_logger import get_logger, setup_server_logging
from utils.storage import append_audit_log, load_audit_history, save_audit_payload

APP_ROOT = Path(__file__).resolve().parent
DEV_LOG_DIR = APP_ROOT / "data" / "dev_logs"
DEV_LOG_DIR.mkdir(parents=True, exist_ok=True)
TRACE_MIRROR_FILE = APP_ROOT / "xf.log"
SERVER_LOG_FILE = setup_server_logging(logging.DEBUG)
LOGGER = get_logger("app")

st.set_page_config(
    page_title="Marketing Agents",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

INDUSTRIES = ["Insurance", "SaaS", "Retail", "BFSI", "Healthcare", "Other"]
REGIONS = ["India", "Global", "US", "SEA", "Europe"]
FOCUS_AREAS = ["Pricing", "Messaging", "Product", "Ads", "Hiring", "PR"]
IMAGE_LIBRARY = {
    "home_geo": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=1200&q=80",
    "home_ci": "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=1200&q=80",
    "geo_setup": "https://images.unsplash.com/photo-1551281044-8b31f73f5afe?auto=format&fit=crop&w=1400&q=80",
    "ci_setup": "https://images.unsplash.com/photo-1552664730-d307ca884978?auto=format&fit=crop&w=1400&q=80",
}

AI_SOV_HELP = (
    "AI Share of Voice: percentage of audited queries where the brand is mentioned. "
    "Higher means stronger visibility in LLM answers."
)
VISIBILITY_HELP = (
    "Visibility Score (0-100): weighted quality score based on mention rate, mention position, "
    "and sentiment. Higher means stronger and more favorable presence."
)
GAP_HELP = (
    "Gap Score: opportunity size where competitors are mentioned and your brand is absent. "
    "Higher score means higher content priority."
)

KNOWN_COMPETITORS = {
    "dettol": ["Lifebuoy", "Savlon", "Lux", "Dove", "Pears"],
    "dove": ["Lux", "Pears", "Nivea", "Fiama", "Santoor"],
    "salesforce": ["HubSpot", "Zoho CRM", "Pipedrive", "Freshsales", "Microsoft Dynamics 365"],
    "hubspot": ["Salesforce", "Zoho CRM", "ActiveCampaign", "Pipedrive", "Freshsales"],
    "zoho": ["Salesforce", "HubSpot", "Pipedrive", "Freshsales", "Monday CRM"],
}

KNOWN_CI_COMPETITORS = {
    "maruti suzuki swift": [
        {"name": "Hyundai i20", "website": "https://www.hyundai.com/in/en/find-a-car/i20/highlights"},
        {"name": "Tata Altroz", "website": "https://cars.tatamotors.com/cars/altroz"},
        {"name": "Maruti Baleno", "website": "https://www.nexaexperience.com/baleno"},
        {"name": "Toyota Glanza", "website": "https://www.toyotabharat.com/showroom/glanza"},
        {"name": "Honda Amaze", "website": "https://www.hondacarindia.com/honda-amaze"},
    ],
    "dettol": [
        {"name": "Lifebuoy", "website": "https://www.lifebuoy.in"},
        {"name": "Savlon", "website": "https://www.savlon.com"},
        {"name": "Lux", "website": "https://www.lux.com/in"},
        {"name": "Dove", "website": "https://www.dove.com/in"},
        {"name": "Pears", "website": "https://www.pears.com"},
    ],
    "salesforce": [
        {"name": "HubSpot", "website": "https://www.hubspot.com"},
        {"name": "Zoho CRM", "website": "https://www.zoho.com/crm"},
        {"name": "Pipedrive", "website": "https://www.pipedrive.com"},
        {"name": "Freshsales", "website": "https://www.freshworks.com/crm"},
        {"name": "Microsoft Dynamics 365", "website": "https://dynamics.microsoft.com"},
    ],
}

BRAND_PROFILE_HINTS = {
    "maruti suzuki swift": {
        "geo": {
            "category": "Hatchback Car",
            "industry": "Retail",
            "region": "India",
            "keywords": [
                "best hatchback in india",
                "swift mileage",
                "swift vs i20",
                "maintenance cost hatchback",
            ],
        },
        "ci": {
            "website": "https://www.marutisuzuki.com/swift",
            "positioning": "High-mileage, city-friendly hatchback with wide service network",
        },
    }
}

CI_BRAND_DEFAULTS = {
    "maruti suzuki swift": {
        "website": "https://www.marutisuzuki.com/swift",
        "positioning": "High-mileage, city-friendly hatchback with wide service network",
    },
    "dettol": {
        "website": "https://www.dettol.co.in",
        "positioning": "Trusted germ-protection personal care brand for everyday family hygiene",
    },
    "salesforce": {
        "website": "https://www.salesforce.com",
        "positioning": "Enterprise CRM platform for sales, service, marketing, and data-driven growth",
    },
}


def apply_openrouter_style() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: radial-gradient(1000px 380px at 8% -6%, rgba(72, 120, 255, 0.14), transparent 52%),
                        radial-gradient(760px 360px at 96% -6%, rgba(57, 203, 180, 0.13), transparent 44%),
                        linear-gradient(180deg, #ffffff 0%, #f7faff 52%, #ffffff 100%);
            color: #0f172a;
        }
        .block-container {
            max-width: 1180px;
            padding-top: 0.6rem;
            padding-bottom: 1.2rem;
        }
        h1, h2, h3, h4, h5, h6, p, label, span {
            color: #0f172a !important;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
            border-right: 1px solid rgba(108, 132, 255, 0.18);
        }
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid rgba(127, 148, 255, 0.28);
            border-radius: 12px;
            padding: 12px;
        }
        .stButton > button, .stDownloadButton > button {
            border-radius: 10px !important;
            border: 1px solid rgba(81, 112, 255, 0.5) !important;
            background: linear-gradient(135deg, #2c66ff 0%, #3f84ff 45%, #19bdb3 100%) !important;
            color: white !important;
            font-weight: 600 !important;
        }
        .or-hero {
            border: 1px solid rgba(120, 142, 255, 0.28);
            border-radius: 16px;
            padding: 18px 20px;
            background: linear-gradient(140deg, rgba(244, 248, 255, 0.95), rgba(255, 255, 255, 0.95));
            margin: 8px 0 14px;
        }
        .or-hero h2 {
            font-size: 1.6rem;
            margin: 0;
            color: #0f172a !important;
        }
        .or-hero p {
            margin: 6px 0 0 0;
            color: #3b4f7a !important;
            font-size: 0.96rem;
        }
        .or-pill-row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }
        .or-pill {
            border: 1px solid rgba(110, 131, 235, 0.34);
            background: rgba(91, 125, 255, 0.08);
            color: #1e2a52;
            border-radius: 999px;
            padding: 4px 10px;
            font-size: 12px;
        }
        .or-sticky-nav {
            position: sticky;
            top: 0;
            z-index: 1000;
            margin: -0.6rem -1rem 0.8rem -1rem;
            padding: 10px 16px;
            backdrop-filter: blur(8px);
            background: rgba(255, 255, 255, 0.92);
            border-bottom: 1px solid rgba(96, 122, 255, 0.20);
        }
        .or-nav-inner {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 18px;
        }
        .or-logo {
            font-weight: 700;
            color: #0b1326;
            text-decoration: none;
            font-size: 15px;
            letter-spacing: 0.2px;
            white-space: nowrap;
        }
        .or-logo-dot {
            color: #2e6bff;
        }
        .or-menu {
            display: flex;
            align-items: center;
            gap: 18px;
            flex-wrap: wrap;
        }
        .or-menu a {
            text-decoration: none;
            color: #2e3d68;
            font-size: 14px;
            padding: 6px 2px 8px;
            border-bottom: 2px solid transparent;
        }
        .or-menu a.active {
            color: #1247df;
            border-bottom-color: #1247df;
            font-weight: 600;
        }
        .or-section-card {
            border: 1px solid rgba(118, 139, 240, 0.20);
            border-radius: 14px;
            background: #ffffff;
            padding: 14px 14px 8px;
            margin: 10px 0;
            box-shadow: 0 8px 24px rgba(49, 80, 180, 0.06);
        }
        .or-agent-label {
            font-size: 0.84rem;
            color: #4a6094 !important;
            margin-bottom: 2px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.4px;
        }
        [data-testid="stSidebar"] * {
            color: #0f172a !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _get_openrouter_client() -> OpenAI | None:
    if not settings.openrouter_api_key:
        return None
    return OpenAI(base_url=settings.openrouter_base_url, api_key=settings.openrouter_api_key)


def suggest_geo_competitors(brand_name: str, category: str, region: str) -> list[str]:
    key = brand_name.strip().lower()
    for known, rivals in KNOWN_COMPETITORS.items():
        if known in key:
            return rivals[:5]

    client = _get_openrouter_client()
    if not client or not brand_name.strip():
        return []
    try:
        prompt = {
            "brand_name": brand_name,
            "category": category,
            "region": region,
            "task": "Return top 5 direct competitors as a JSON array of strings only.",
        }
        response = client.chat.completions.create(
            model=settings.openrouter_model,
            messages=[
                {"role": "system", "content": "You are a market analyst. Return valid JSON only."},
                {"role": "user", "content": json.dumps(prompt)},
            ],
            temperature=0.2,
        )
        parsed = json.loads(response.choices[0].message.content or "[]")
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()][:5]
    except Exception:
        return []
    return []


def suggest_ci_competitors(brand_name: str, website: str, positioning: str) -> list[dict[str, str]]:
    key = brand_name.strip().lower()
    for known, rivals in KNOWN_CI_COMPETITORS.items():
        if known in key:
            return rivals[:8]

    client = _get_openrouter_client()
    if not client or not brand_name.strip():
        return []
    try:
        prompt = {
            "brand_name": brand_name,
            "website": website,
            "positioning": positioning,
            "task": "Suggest top direct competitors with likely official websites.",
            "output": [{"name": "string", "website": "https://..."}],
            "count": 8,
        }
        response = client.chat.completions.create(
            model=settings.openrouter_model,
            messages=[
                {"role": "system", "content": "Return only valid JSON array with name and website."},
                {"role": "user", "content": json.dumps(prompt)},
            ],
            temperature=0.2,
        )
        parsed = json.loads(response.choices[0].message.content or "[]")
        if isinstance(parsed, list):
            out = []
            for item in parsed:
                if not isinstance(item, dict):
                    continue
                name = str(item.get("name", "")).strip()
                web = str(item.get("website", "")).strip()
                if name and web:
                    out.append({"name": name, "website": web})
            return out[:8]
    except Exception:
        return []
    return []


def init_state() -> None:
    defaults = {
        "nav_page": "Home",
        "geo_context": None,
        "geo_queries": [],
        "geo_audit": None,
        "geo_stage": "brand",
        "gsc_properties": [],
        "gsc_selected_property": None,
        "gsc_status_message": "",
        "use_gsc_enrichment": False,
        "geo_query_count": 10,
        "geo_brand_name": "",
        "geo_category": "",
        "geo_industry": INDUSTRIES[0],
        "geo_region": REGIONS[0],
        "geo_competitors_input": "",
        "geo_keywords_input": "",
        "geo_competitors_prefill": None,
        "ci_stage": "brand",
        "ci_result": None,
        "ci_config": None,
        "ci_own_brand_name": "",
        "ci_own_brand_website": "",
        "ci_own_brand_positioning": "",
        "ci_last_autofilled_brand": "",
        "ci_brand_website_prefill": None,
        "ci_brand_positioning_prefill": None,
        "ci_competitors_input": "",
        "ci_watch_phrases": "",
        "ci_competitors_prefill": None,
        "verbose_mode": False,
        "app_logs": [],
        "current_dev_log_file": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def score_badge(score: float) -> str:
    if score >= 65:
        return "🟢"
    if score >= 45:
        return "🟡"
    return "🔴"


def log_event(message: str, level: str = "INFO") -> None:
    stamp = datetime.now().strftime("%H:%M:%S")
    logs = st.session_state.app_logs
    logs.append(f"[{stamp}] [{level}] {message}")
    st.session_state.app_logs = logs[-400:]
    if level == "ERROR":
        LOGGER.error(message)
    elif level == "WARN":
        LOGGER.warning(message)
    else:
        LOGGER.info(message)
    log_file = st.session_state.current_dev_log_file
    if log_file:
        try:
            with Path(log_file).open("a", encoding="utf-8") as file:
                file.write(f"[{stamp}] [{level}] {message}\n")
        except OSError:
            pass
    if st.session_state.verbose_mode:
        try:
            with TRACE_MIRROR_FILE.open("a", encoding="utf-8") as file:
                file.write(f"[{stamp}] [{level}] {message}\n")
        except OSError:
            pass


def start_dev_log_run(agent: str, context_id: str) -> None:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = DEV_LOG_DIR / f"{stamp}_{agent}_{context_id}.log"
    st.session_state.current_dev_log_file = str(file_path)
    with file_path.open("w", encoding="utf-8") as file:
        file.write(f"# Development Trace Log\n# agent={agent}\n# context_id={context_id}\n# started={stamp}\n\n")
    if st.session_state.verbose_mode:
        with TRACE_MIRROR_FILE.open("a", encoding="utf-8") as file:
            file.write(
                f"\n# ---- New Verbose Run ----\n# started={stamp}\n# agent={agent}\n# context_id={context_id}\n"
            )


def render_logs_panel() -> None:
    if not st.session_state.verbose_mode:
        return
    st.markdown("### Processing Logs")
    if st.session_state.current_dev_log_file:
        st.caption(f"Persistent trace file: {st.session_state.current_dev_log_file}")
    with st.container(border=True):
        logs = st.session_state.app_logs or ["[No logs yet] Toggle is active and waiting for events."]
        st.code("\n".join(logs[-120:]), language="text")
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("Clear Logs", use_container_width=True, key="clear_logs_btn"):
                st.session_state.app_logs = []
                st.rerun()
        with c2:
            st.download_button(
                "Download Logs",
                data="\n".join(logs),
                file_name=f"marketingagents_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True,
            )


def render_steps(current_step: str, step_labels: list[tuple[str, str]]) -> None:
    keys = [item[0] for item in step_labels]
    current_index = keys.index(current_step) if current_step in keys else 0
    cols = st.columns(len(step_labels))
    for idx, (_, label) in enumerate(step_labels):
        status = "Done" if idx < current_index else "Current" if idx == current_index else "Pending"
        cols[idx].markdown(f"**Step {idx + 1}**  \n{label}  \n`{status}`")
    st.progress((current_index + 1) / len(step_labels))


def _logo_from_website(website: str, competitor_name: str = "") -> str:
    try:
        domain = urlparse(website).netloc.replace("www.", "").strip()
    except Exception:
        domain = ""
    if domain:
        return f"https://www.google.com/s2/favicons?domain={domain}&sz=128"
    if competitor_name:
        return f"https://ui-avatars.com/api/?name={quote_plus(competitor_name)}&background=2f67ff&color=ffffff&size=128"
    return "https://ui-avatars.com/api/?name=Brand&background=2f67ff&color=ffffff&size=128"


def build_marketing_summary(item: dict) -> str:
    competitor = item.get("competitor_name", "Competitor")
    cvs = item.get("cvs_score", 0)
    threat = str(item.get("threat_level", "low")).upper()
    speed = str(item.get("speed_of_movement", "moderate")).upper()
    signal = item.get("strategic_interpretation", "") or item.get("what_changed", "")
    response = item.get("recommended_response", "")
    return (
        f"{competitor} is at CVS {cvs} ({speed}) with {threat} threat intensity. "
        f"Marketing read: {signal or 'message activity is increasing across tracked channels.'} "
        f"Action: {response or 'counter with stronger proof-led differentiation.'}"
    )


def _pricing_band_from_cvs(cvs: float) -> str:
    if cvs >= 70:
        return "₹12K–₹25K (Premium)"
    if cvs >= 45:
        return "₹6K–₹15K (Mid-Premium)"
    return "₹2K–₹10K (Value-Mid)"


def _engagement_from_cvs(cvs: float) -> str:
    if cvs >= 70:
        return "Very High"
    if cvs >= 55:
        return "High"
    if cvs >= 35:
        return "Medium"
    return "Low"


def build_generic_ci_dashboard(result) -> dict:
    own_brand = result.own_brand.get("name", "Your Brand")
    comps = result.competitors[:4]
    if not comps:
        return {}

    top_comp = comps[0]
    yoy_candidates = []
    for item in comps:
        yoy = round((float(item.get("cvs_score", 0)) - 45.0) / 8.0, 1)
        yoy_candidates.append((item["competitor_name"], yoy))
    fastest = max(yoy_candidates, key=lambda x: x[1])[0] if yoy_candidates else top_comp["competitor_name"]

    own_market_share = round(max(18.0, 34.0 - (sum(float(c["cvs_score"]) for c in comps) / (len(comps) * 35))), 1)
    remaining = max(100.0 - own_market_share, 10.0)
    weights = [max(float(item.get("cvs_score", 0)), 1.0) for item in comps]
    total_weight = sum(weights)

    market_rows = [
        {
            "Brand": own_brand,
            "Market Share": f"{own_market_share}%",
            "YoY Growth": f"{round(-max(0.5, (sum(y for _, y in yoy_candidates) / max(len(yoy_candidates), 1)) / 2), 1)}%",
        }
    ]
    for item, weight in zip(comps, weights):
        share = round((weight / total_weight) * remaining, 1)
        yoy = round((float(item.get("cvs_score", 0)) - 45.0) / 8.0, 1)
        sign = "+" if yoy >= 0 else ""
        market_rows.append(
            {
                "Brand": item["competitor_name"],
                "Market Share": f"{share}%",
                "YoY Growth": f"{sign}{yoy}%",
            }
        )

    pricing_rows = []
    for item in [ {"competitor_name": own_brand, "cvs_score": 55}, *comps ]:
        cvs = float(item.get("cvs_score", 0))
        pricing_rows.append(
            {
                "Brand": item["competitor_name"],
                "Core Offer Pricing": _pricing_band_from_cvs(cvs),
                "Value Positioning": "Premium disruptor" if cvs >= 70 else "Premium-mass hybrid" if cvs >= 45 else "Value-focused",
            }
        )

    campaign_rows = []
    for item in comps:
        campaign_rows.append(
            {
                "Brand": item["competitor_name"],
                "Key Campaign Signal": item.get("what_changed", "Messaging refresh detected"),
                "Strategy": item.get("strategic_interpretation", "Positioning optimization"),
            }
        )

    digital_rows = []
    for item in [ {"competitor_name": own_brand, "cvs_score": 52, "threat_level": "medium"}, *comps ]:
        cvs = float(item.get("cvs_score", 0))
        digital_rows.append(
            {
                "Brand": item["competitor_name"],
                "Engagement Signal": _engagement_from_cvs(cvs),
                "Website Momentum Score": round(min(9.5, max(6.5, 6.0 + cvs / 20.0)), 1),
                "Threat": str(item.get("threat_level", "medium")).upper(),
            }
        )

    innovation_lines = []
    for item in comps:
        signals = item.get("key_signals", [])
        line = f"{item['competitor_name']}: {', '.join(signals[:2]) if signals else 'feature and messaging updates detected'}"
        innovation_lines.append(line)

    alerts = []
    for item in comps:
        if float(item.get("cvs_score", 0)) >= 60:
            alerts.append(f"🚨 {item['competitor_name']} moving aggressively ({item['cvs_category']}).")
        elif str(item.get("threat_level", "")).lower() == "medium":
            alerts.append(f"⚠️ {item['competitor_name']} showing steady acceleration.")
    if not alerts:
        alerts.append("ℹ️ No critical escalation signals this cycle.")

    return {
        "own_brand": own_brand,
        "market_position": "#1 (current monitored set)" if own_market_share >= 25 else "Competitive",
        "threat_trend": "Increasing" if any(float(c["cvs_score"]) >= 55 for c in comps) else "Stable",
        "key_competitor": top_comp["competitor_name"],
        "fastest_growing_competitor": fastest,
        "market_share_trend": market_rows[0]["YoY Growth"],
        "market_table": market_rows,
        "pricing_table": pricing_rows,
        "campaign_table": campaign_rows,
        "digital_table": digital_rows,
        "innovation_lines": innovation_lines,
        "alerts": alerts,
    }


def _guess_brand_website(brand_name: str) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "" for ch in brand_name)
    if not slug:
        return ""
    if any(token in brand_name.lower() for token in ["maruti", "tata", "hyundai", "mahindra"]):
        return f"https://www.{slug}.co.in"
    return f"https://www.{slug}.com"


def suggest_ci_brand_details(brand_name: str) -> tuple[str, str]:
    key = brand_name.strip().lower()
    if not key:
        return "", ""
    if key in CI_BRAND_DEFAULTS:
        data = CI_BRAND_DEFAULTS[key]
        return data["website"], data["positioning"]

    website = _guess_brand_website(brand_name)
    positioning = f"{brand_name.strip()} brand focused on value, trust, and customer-centric differentiation."
    return website, positioning


def render_header() -> None:
    st.markdown(
        """
        <div class="or-hero">
          <h2 style="margin:0;">Marketing Agents Workspace</h2>
          <p>
            Unified interface for GEO visibility audits and competitor intelligence monitoring.
          </p>
          <div class="or-pill-row">
            <span class="or-pill">One Dashboard</span>
            <span class="or-pill">Optional Integrations</span>
            <span class="or-pill">Marketing-First Insights</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    ctl_col1, ctl_col2 = st.columns([4, 1])
    with ctl_col1:
        st.caption("Use verbose logs to track key processing events and transitions.")
    with ctl_col2:
        st.toggle("Verbose logs", key="verbose_mode")


def render_footer() -> None:
    st.markdown("---")
    st.caption(f"MarketngAgents • Server logs: {SERVER_LOG_FILE}")


def sync_nav_from_query_params() -> None:
    page = st.query_params.get("page")
    valid = {"Home", "GEO Agent", "Competitor Intelligence Agent", "History"}
    if page in valid and page != st.session_state.nav_page:
        st.session_state.nav_page = page


def render_sticky_navigation() -> None:
    nav_items = ["Home", "GEO Agent", "Competitor Intelligence Agent", "History"]
    links = []
    for item in nav_items:
        css_class = "active" if st.session_state.nav_page == item else ""
        links.append(f'<a class="{css_class}" href="?page={quote(item)}">{item}</a>')

    st.markdown(
        f"""
        <div class="or-sticky-nav">
          <div class="or-nav-inner">
            <a class="or-logo" href="?page=Home">
              <span style="display:inline-flex;align-items:center;gap:8px;">
                <span style="width:20px;height:20px;border-radius:6px;background:linear-gradient(135deg,#2f67ff,#17c2b4);display:inline-block;"></span>
                <span>Marketing<span class="or-logo-dot">Agents</span></span>
              </span>
            </a>
            <div class="or-menu">
              {"".join(links)}
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def home_page() -> None:
    st.markdown('<div class="or-agent-label">Home</div>', unsafe_allow_html=True)
    st.subheader("Choose Your Marketing Agent")
    stat1, stat2, stat3 = st.columns(3)
    with stat1:
        st.metric("Agents", "2")
    with stat2:
        st.metric("Integrations", "Optional")
    with stat3:
        st.metric("Storage", "Local JSON")

    st.markdown("### Agent Overview")
    card_col1, card_col2 = st.columns(2)
    with card_col1:
        st.markdown('<div class="or-section-card">', unsafe_allow_html=True)
        st.image(IMAGE_LIBRARY["home_geo"], caption="GEO Agent")
        st.markdown("**What it does**: Audits how your brand appears in LLM answers.")
        st.markdown("**Inputs**: Brand, category, region, competitors, topics, query count.")
        st.markdown("**Outputs**: AI Share of Voice, Visibility Score, topic gaps, action plan.")
        st.markdown("**How it helps**: Prioritizes marketing content that improves AI discoverability.")
        if st.button("Open GEO Agent", use_container_width=True, key="open_geo_agent"):
            st.session_state.nav_page = "GEO Agent"
            st.query_params["page"] = "GEO Agent"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with card_col2:
        st.markdown('<div class="or-section-card">', unsafe_allow_html=True)
        st.image(IMAGE_LIBRARY["home_ci"], caption="Competitor Intelligence Agent")
        st.markdown("**What it does**: Monitors competitor changes and generates strategic weekly digest.")
        st.markdown("**Inputs**: Your brand profile, competitor names/URLs, watch phrases, focus areas.")
        st.markdown("**Outputs**: CVS scorecards, threat levels, deep dives, recommended actions.")
        st.markdown("**How it helps**: Helps marketers react faster to messaging and pricing shifts.")
        if st.button("Open Competitor Intelligence Agent", use_container_width=True, key="open_ci_agent"):
            st.session_state.nav_page = "Competitor Intelligence Agent"
            st.query_params["page"] = "Competitor Intelligence Agent"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### Placeholder Agents (Coming Soon)")
    st.caption("These are visible placeholders. You can wire the full agent flows later.")
    p1, p2 = st.columns(2)
    with p1:
        st.markdown('<div class="or-section-card">', unsafe_allow_html=True)
        st.markdown("#### ✍️ Content Agent (Placeholder)")
        st.markdown("- Generates email copy, push notifications, and ad headlines")
        st.markdown("- Focus: personalization by audience segment and funnel stage")
        st.caption("Outcome: Hyper-personalized content at scale")
        st.button("Coming Soon: Content Agent", key="ph_content_agent", use_container_width=True, disabled=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with p2:
        st.markdown('<div class="or-section-card">', unsafe_allow_html=True)
        st.markdown("#### 🎨 Creative Agent (Placeholder)")
        st.markdown("- Produces image/banner variations for campaigns")
        st.markdown("- Focus: fast creative iteration by channel")
        st.caption("Outcome: More creative options with lower production cycle time")
        st.button("Coming Soon: Creative Agent", key="ph_creative_agent", use_container_width=True, disabled=True)
        st.markdown("</div>", unsafe_allow_html=True)

    p3, p4 = st.columns(2)
    with p3:
        st.markdown('<div class="or-section-card">', unsafe_allow_html=True)
        st.markdown("#### 🧪 Experimentation Agent (Placeholder)")
        st.markdown("- Auto-generates A/B variants for copy and creatives")
        st.markdown("- Focus: statistical winner selection and rollout")
        st.caption("Outcome: Faster optimization loops across campaigns")
        st.button("Coming Soon: Experimentation Agent", key="ph_experiment_agent", use_container_width=True, disabled=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with p4:
        st.markdown('<div class="or-section-card">', unsafe_allow_html=True)
        st.markdown("#### 🧩 Landing Page Optimization Agent (Placeholder)")
        st.markdown("- Recommends and tests layout/copy blocks for conversion lift")
        st.markdown("- Focus: CTA clarity, proof placement, and friction removal")
        st.caption("Outcome: Better CVR from paid and organic traffic")
        st.button("Coming Soon: LPO Agent", key="ph_lpo_agent", use_container_width=True, disabled=True)
        st.markdown("</div>", unsafe_allow_html=True)


def _gsc_panel() -> None:
    with st.expander("Optional Integration: Google Search Console", expanded=False):
        status = get_gsc_status()
        st.info(status.message)
        if not status.connected:
            st.session_state.use_gsc_enrichment = False

        st.checkbox(
            "Use GSC enrichment in GEO audit",
            key="use_gsc_enrichment",
            disabled=not status.connected,
            help="Runs only when Google auth is valid and a property is selected.",
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Connect Google Search Console", use_container_width=True):
                ok, message = authenticate_gsc()
                st.session_state.gsc_status_message = message
                if ok:
                    st.session_state.gsc_properties = list_gsc_properties()
                    if st.session_state.gsc_properties:
                        st.session_state.gsc_selected_property = st.session_state.gsc_properties[0]
                st.rerun()
        with col2:
            if st.button("Refresh GSC Properties", use_container_width=True):
                try:
                    st.session_state.gsc_properties = list_gsc_properties()
                    st.session_state.gsc_status_message = (
                        f"Loaded {len(st.session_state.gsc_properties)} GSC properties."
                    )
                    if st.session_state.gsc_properties and not st.session_state.gsc_selected_property:
                        st.session_state.gsc_selected_property = st.session_state.gsc_properties[0]
                except Exception as exc:
                    st.session_state.gsc_status_message = f"Unable to fetch properties: {exc}"
                st.rerun()

        if st.session_state.gsc_status_message:
            st.caption(st.session_state.gsc_status_message)

        if st.session_state.gsc_properties:
            current = st.session_state.gsc_selected_property
            idx = (
                st.session_state.gsc_properties.index(current)
                if current in st.session_state.gsc_properties
                else 0
            )
            st.session_state.gsc_selected_property = st.selectbox(
                "GSC Property",
                st.session_state.gsc_properties,
                index=idx,
            )


def geo_brand_step() -> None:
    render_steps(
        st.session_state.geo_stage,
        [("brand", "Your Brand"), ("competitors", "Your Competitors"), ("analysis", "Analysis"), ("results", "Dashboard")],
    )
    st.subheader("GEO Agent • Step 1: Your Brand")
    with st.form("geo_brand_form"):
        col1, col2 = st.columns(2)
        with col1:
            brand_name = st.text_input("Brand Name *", key="geo_brand_name")
            category = st.text_input("Product Category *", key="geo_category")
        with col2:
            industry = st.selectbox("Industry Vertical *", INDUSTRIES, key="geo_industry")
            region = st.selectbox("Region / Market *", REGIONS, key="geo_region")

        next_step = st.form_submit_button("Step 1 → Step 2: Add Competitors", use_container_width=True)

    if not next_step:
        return
    if not brand_name.strip() or not category.strip():
        st.error("Please fill your brand and category to continue.")
        log_event("GEO Step 1 validation failed: missing brand or category.", "WARN")
        return

    log_event(f"GEO Step 1 completed for brand '{brand_name.strip()}'.")
    profile = BRAND_PROFILE_HINTS.get(brand_name.strip().lower())
    if profile:
        st.session_state.geo_category = st.session_state.geo_category or profile["geo"]["category"]
        st.session_state.geo_industry = st.session_state.geo_industry or profile["geo"]["industry"]
        st.session_state.geo_region = st.session_state.geo_region or profile["geo"]["region"]
        if not st.session_state.geo_keywords_input:
            st.session_state.geo_keywords_input = "\n".join(profile["geo"]["keywords"])

    suggestions = suggest_geo_competitors(
        brand_name=st.session_state.geo_brand_name,
        category=st.session_state.geo_category,
        region=st.session_state.geo_region,
    )
    if suggestions and not st.session_state.geo_competitors_input:
        st.session_state.geo_competitors_prefill = "\n".join(suggestions)
        log_event(f"GEO competitor auto-suggestion filled {len(suggestions)} competitors.")

    st.session_state.geo_stage = "competitors"
    st.rerun()


def geo_competitors_step() -> None:
    if st.session_state.geo_competitors_prefill is not None:
        st.session_state.geo_competitors_input = st.session_state.geo_competitors_prefill
        st.session_state.geo_competitors_prefill = None

    render_steps(
        st.session_state.geo_stage,
        [("brand", "Your Brand"), ("competitors", "Your Competitors"), ("analysis", "Analysis"), ("results", "Dashboard")],
    )
    st.subheader("GEO Agent • Step 2: Your Competitors")
    with st.form("geo_competitor_form"):
        competitors_input = st.text_area(
            "Competitors * (1-5, one per line)",
            height=170,
            key="geo_competitors_input",
        )
        keywords_input = st.text_area(
            "Target Keywords / Topics (up to 10, one per line)",
            height=150,
            key="geo_keywords_input",
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            back = st.form_submit_button("Step 2 → Step 1: Edit Brand", use_container_width=True)
        with c2:
            suggest = st.form_submit_button("Step 2: Re-Suggest Competitors", use_container_width=True)
        with c3:
            next_step = st.form_submit_button("Step 2 → Step 3: Configure Analysis", use_container_width=True)

    if back:
        log_event("GEO moved from Step 2 back to Step 1.")
        st.session_state.geo_stage = "brand"
        st.rerun()
    if suggest:
        suggestions = suggest_geo_competitors(
            brand_name=st.session_state.geo_brand_name,
            category=st.session_state.geo_category,
            region=st.session_state.geo_region,
        )
        if suggestions:
            st.session_state.geo_competitors_prefill = "\n".join(suggestions)
            st.success("Competitors re-suggested.")
            log_event(f"GEO Step 2 re-suggested {len(suggestions)} competitors.")
        else:
            st.warning("Could not fetch suggestions now.")
            log_event("GEO Step 2 competitor re-suggestion failed.", "WARN")
        st.rerun()
    if not next_step:
        return

    competitors = [row.strip() for row in competitors_input.splitlines() if row.strip()][:5]
    if not competitors:
        st.error("Add at least one competitor.")
        log_event("GEO Step 2 validation failed: no competitors entered.", "WARN")
        return
    log_event(f"GEO Step 2 completed with {len(competitors)} competitors.")
    st.session_state.geo_stage = "analysis"
    st.rerun()


def geo_analysis_step() -> None:
    render_steps(
        st.session_state.geo_stage,
        [("brand", "Your Brand"), ("competitors", "Your Competitors"), ("analysis", "Analysis"), ("results", "Dashboard")],
    )
    st.subheader("GEO Agent • Step 3: Analysis")
    _gsc_panel()
    query_count = st.number_input(
        "Number of Queries",
        min_value=3,
        max_value=30,
        value=int(st.session_state.geo_query_count),
        step=1,
    )
    st.session_state.geo_query_count = int(query_count)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Step 3 → Step 2: Edit Competitors", use_container_width=True):
            log_event("GEO moved from Step 3 back to Step 2.")
            st.session_state.geo_stage = "competitors"
            st.rerun()
    with col2:
        if st.button("Step 3 → Step 4: Run Analysis", use_container_width=True):
            competitors = [row.strip() for row in st.session_state.geo_competitors_input.splitlines() if row.strip()][:5]
            keywords = [row.strip() for row in st.session_state.geo_keywords_input.splitlines() if row.strip()][:10]
            context = BrandContext(
                brand_name=st.session_state.geo_brand_name.strip(),
                category=st.session_state.geo_category.strip(),
                industry=st.session_state.geo_industry,
                region=st.session_state.geo_region,
                competitors=competitors,
                keywords=keywords,
            )
            st.session_state.geo_context = context
            st.session_state.geo_queries = generate_query_set(context, total_queries=int(query_count))
            log_event(
                f"GEO Step 3 started analysis with {len(st.session_state.geo_queries)} queries "
                f"and {len(competitors)} competitors."
            )
            st.session_state.geo_stage = "running"
            st.rerun()


def geo_running_screen() -> None:
    context: BrandContext = st.session_state.geo_context
    queries: list[QueryItem] = st.session_state.geo_queries

    st.subheader("GEO Agent • Running")
    status = st.empty()
    progress = st.progress(0)
    log_box = st.empty()
    logs: list[str] = []

    def on_progress(current: int, total: int, query_text: str) -> None:
        progress.progress(int((current / total) * 100))
        status.markdown(f"Querying LLMs... {current}/{total}")
        logs.append(f"{current:02d}/{total:02d} {query_text}")
        log_box.code("\n".join(logs[-8:]))
        log_event(f"GEO query processed {current}/{total}: {query_text[:90]}")

    gsc_insights: list[dict[str, str | int | float]] = []
    gsc_enabled = bool(st.session_state.use_gsc_enrichment)
    selected_property = st.session_state.gsc_selected_property
    if gsc_enabled and get_gsc_status().connected and selected_property:
        try:
            gsc_insights = fetch_top_queries(selected_property, days=30, row_limit=20)
            log_event(f"GEO loaded {len(gsc_insights)} GSC insights from {selected_property}.")
        except Exception as exc:
            st.warning(f"GSC enrichment skipped: {exc}")
            log_event(f"GEO GSC enrichment skipped: {exc}", "WARN")

    start_dev_log_run("geo", st.session_state.geo_context.audit_id if st.session_state.geo_context else "unknown")
    log_event("GEO runtime started.", "INFO")
    try:
        log_event("GEO run initiated.")
        audit = run_full_audit(
            context,
            queries,
            progress_callback=on_progress,
            gsc_insights=gsc_insights,
            debug_callback=log_event if st.session_state.verbose_mode else None,
        )
    except Exception as exc:
        st.error(f"GEO run failed: {exc}")
        log_event(f"GEO run failed: {exc}", "ERROR")
        if st.button("Back"):
            st.session_state.geo_stage = "analysis"
            st.rerun()
        return

    payload = audit.to_dict()
    output_path = save_audit_payload(context.audit_id, payload)
    append_audit_log(
        {
            "agent": "geo",
            "audit_id": context.audit_id,
            "brand_name": context.brand_name,
            "total_queries": audit.score.total_queries,
            "runtime_seconds": audit.score.runtime_seconds,
            "result_file": str(output_path),
            "gsc_enabled": bool(gsc_insights),
        }
    )

    st.session_state.geo_audit = audit
    log_event(
        f"GEO run complete: visibility={audit.score.visibility_score}, sov={audit.score.ai_sov_pct}, "
        f"runtime={audit.score.runtime_seconds}s."
    )
    st.session_state.geo_stage = "results"
    st.rerun()


def geo_results_screen() -> None:
    audit = st.session_state.geo_audit
    context: BrandContext = st.session_state.geo_context

    render_steps(
        "results",
        [("brand", "Your Brand"), ("competitors", "Your Competitors"), ("analysis", "Analysis"), ("results", "Dashboard")],
    )
    st.subheader("GEO Agent • Results Dashboard")
    st.caption(
        f"{context.brand_name} • {datetime.now().strftime('%Y-%m-%d %H:%M')} • "
        f"{audit.score.total_queries} queries • {audit.score.runtime_seconds:.1f}s"
    )

    with st.expander("How to read these numbers"):
        st.markdown(
            "- **AI Share of Voice (%)**: percent of prompts where brand appears.\n"
            "- **Visibility Score (0-100)**: mention rate + position + sentiment quality.\n"
            "- **Gap Score**: topic opportunity where competitors are present and your brand is absent."
        )

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("AI Share of Voice")
        st.metric(
            context.brand_name,
            f"{audit.score.ai_sov_pct}% {score_badge(audit.score.ai_sov_pct)}",
            help=AI_SOV_HELP,
        )
        for name, score in audit.score.competitor_scores.items():
            st.metric(name, f"{score.ai_sov_pct}% {score_badge(score.ai_sov_pct)}", help=AI_SOV_HELP)

    with col2:
        st.subheader("Visibility Score")
        st.metric(
            context.brand_name,
            f"{audit.score.visibility_score}/100 {score_badge(audit.score.visibility_score)}",
            help=VISIBILITY_HELP,
        )
        for name, score in audit.score.competitor_scores.items():
            st.metric(name, f"{score.visibility_score}/100 {score_badge(score.visibility_score)}", help=VISIBILITY_HELP)

    st.subheader("Topic Gap Heatmap")
    if audit.score.gaps:
        gap_table = pd.DataFrame(
            [
                {
                    "Topic": gap.topic,
                    "Gap Score": gap.gap_score,
                    "Dominant Competitor": gap.dominant_competitor,
                    "Priority": "High" if gap.gap_score >= 3 else "Medium",
                }
                for gap in audit.score.gaps
            ]
        )
        st.dataframe(
            gap_table,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Gap Score": st.column_config.NumberColumn("Gap Score", format="%.2f", help=GAP_HELP),
            },
        )
    else:
        st.success("No critical topic gaps found.")

    if audit.gsc_insights:
        st.subheader("Owned Search Signals (GSC Optional)")
        st.dataframe(pd.DataFrame(audit.gsc_insights), use_container_width=True, hide_index=True)

    st.subheader("Action Plan")
    for idx, item in enumerate(audit.recommendations, start=1):
        with st.container(border=True):
            st.markdown(f"**{idx}. {item.get('topic', 'Untitled topic')}**")
            st.write(f"Format: {item.get('content_format', 'Content page')}")
            st.write(f"Why: {item.get('why_this_works', '-')}")
            st.write(f"Urgency: {item.get('urgency', 'Watch')}")
            st.write(f"Competitor to displace: {item.get('competitor_to_displace', 'N/A')}")

    with st.expander("Raw GEO Log"):
        st.dataframe(pd.DataFrame([item.to_dict() for item in audit.parsed_results]), use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Run New GEO Audit", use_container_width=True):
            st.session_state.geo_context = None
            st.session_state.geo_queries = []
            st.session_state.geo_audit = None
            st.session_state.geo_stage = "brand"
            st.rerun()
    with col2:
        if st.button("Step 4: Back to Home", use_container_width=True):
            st.session_state.nav_page = "Home"
            st.query_params["page"] = "Home"
            st.rerun()


def geo_agent_page() -> None:
    stage = st.session_state.geo_stage
    if stage == "brand":
        geo_brand_step()
    elif stage == "competitors":
        geo_competitors_step()
    elif stage == "analysis":
        geo_analysis_step()
    elif stage == "running":
        geo_running_screen()
    elif stage == "results":
        geo_results_screen()


def ci_brand_step() -> None:
    render_steps(
        st.session_state.ci_stage,
        [("brand", "Your Brand"), ("competitors", "Your Competitors"), ("analysis", "Analysis"), ("digest", "Dashboard")],
    )
    st.subheader("Competitor Intelligence • Step 1: Your Brand")

    if st.session_state.ci_brand_website_prefill is not None:
        st.session_state.ci_own_brand_website = st.session_state.ci_brand_website_prefill
        st.session_state.ci_brand_website_prefill = None
    if st.session_state.ci_brand_positioning_prefill is not None:
        st.session_state.ci_own_brand_positioning = st.session_state.ci_brand_positioning_prefill
        st.session_state.ci_brand_positioning_prefill = None

    current_brand = st.session_state.ci_own_brand_name.strip()
    should_autofill = (
        current_brand
        and current_brand.lower() != st.session_state.ci_last_autofilled_brand
        and (not st.session_state.ci_own_brand_website.strip() or not st.session_state.ci_own_brand_positioning.strip())
    )
    if should_autofill:
        website, positioning = suggest_ci_brand_details(current_brand)
        has_prefill_update = False
        if not st.session_state.ci_own_brand_website.strip() and website:
            st.session_state.ci_brand_website_prefill = website
            has_prefill_update = True
        if not st.session_state.ci_own_brand_positioning.strip() and positioning:
            st.session_state.ci_brand_positioning_prefill = positioning
            has_prefill_update = True
        st.session_state.ci_last_autofilled_brand = current_brand.lower()
        if has_prefill_update:
            st.rerun()

    with st.form("ci_brand_form"):
        own_brand_name = st.text_input("Your Brand Name *", key="ci_own_brand_name")
        own_brand_website = st.text_input(
            "Your Brand Website *",
            placeholder="https://example.com",
            key="ci_own_brand_website",
        )
        own_brand_positioning = st.text_area(
            "Your Positioning (1 line)",
            height=80,
            key="ci_own_brand_positioning",
        )
        st.caption("Brand URL and positioning are auto-filled from brand name. You can edit both fields.")
        next_step = st.form_submit_button("Step 1 → Step 2: Add Competitors", use_container_width=True)

    if not next_step:
        return
    if not own_brand_name.strip():
        st.error("Please enter your brand name.")
        log_event("CI Step 1 validation failed: missing brand name.", "WARN")
        return

    log_event(f"CI Step 1 completed for brand '{own_brand_name.strip()}'.")
    profile = BRAND_PROFILE_HINTS.get(own_brand_name.strip().lower())
    website = own_brand_website.strip()
    positioning = own_brand_positioning.strip()
    if profile:
        website = website or profile["ci"]["website"]
        positioning = positioning or profile["ci"]["positioning"]
        missing_profile_fill = (
            (not own_brand_website.strip() and bool(website))
            or (not own_brand_positioning.strip() and bool(positioning))
        )
        if missing_profile_fill:
            st.session_state.ci_brand_website_prefill = website
            st.session_state.ci_brand_positioning_prefill = positioning
            st.info("Brand details auto-filled. Review and click Step 1 button again.")
            st.rerun()

    suggestions = suggest_ci_competitors(
        brand_name=own_brand_name,
        website=website,
        positioning=positioning,
    )
    if suggestions and not st.session_state.ci_competitors_input:
        st.session_state.ci_competitors_prefill = "\n".join(
            f"{item['name']},{item['website']}" for item in suggestions
        )
        log_event(f"CI competitor auto-suggestion filled {len(suggestions)} competitors with URLs.")
    st.session_state.ci_stage = "competitors"
    st.rerun()


def ci_competitors_step() -> None:
    if st.session_state.ci_competitors_prefill is not None:
        st.session_state.ci_competitors_input = st.session_state.ci_competitors_prefill
        st.session_state.ci_competitors_prefill = None

    render_steps(
        st.session_state.ci_stage,
        [("brand", "Your Brand"), ("competitors", "Your Competitors"), ("analysis", "Analysis"), ("digest", "Dashboard")],
    )
    st.subheader("Competitor Intelligence • Step 2: Your Competitors")
    with st.form("ci_competitor_form"):
        competitors_input = st.text_area(
            "Competitors (up to 8, one per line as Name,URL) *",
            placeholder="Competitor A,https://comp-a.com\nCompetitor B,https://comp-b.com",
            height=180,
            key="ci_competitors_input",
        )
        watch_phrases = st.text_area(
            "Watch Phrases (one per line, optional)",
            height=100,
            key="ci_watch_phrases",
        )
        focus_areas = st.multiselect("Focus Areas", FOCUS_AREAS, default=["Messaging", "Pricing", "Product"])

        c1, c2, c3 = st.columns(3)
        with c1:
            back = st.form_submit_button("Step 2 → Step 1: Edit Brand", use_container_width=True)
        with c2:
            suggest = st.form_submit_button("Step 2: Re-Suggest Competitors", use_container_width=True)
        with c3:
            next_step = st.form_submit_button("Step 2 → Step 3: Configure Analysis", use_container_width=True)

    if back:
        log_event("CI moved from Step 2 back to Step 1.")
        st.session_state.ci_stage = "brand"
        st.rerun()
    if suggest:
        suggestions = suggest_ci_competitors(
            brand_name=st.session_state.ci_own_brand_name,
            website=st.session_state.ci_own_brand_website,
            positioning=st.session_state.ci_own_brand_positioning,
        )
        if suggestions:
            st.session_state.ci_competitors_prefill = "\n".join(
                f"{item['name']},{item['website']}" for item in suggestions
            )
            st.success("Competitors re-suggested.")
            log_event(f"CI Step 2 re-suggested {len(suggestions)} competitors with URLs.")
        else:
            st.warning("Could not fetch suggestions now.")
            log_event("CI Step 2 competitor re-suggestion failed.", "WARN")
        st.rerun()
    if not next_step:
        return

    competitors: list[dict] = []
    for line in competitors_input.splitlines():
        row = line.strip()
        if not row or "," not in row:
            continue
        name, website = row.split(",", 1)
        name, website = name.strip(), website.strip()
        if name and website:
            competitors.append({"name": name, "website": website})
    if not competitors:
        st.error("Add at least one competitor as Name,URL.")
        log_event("CI Step 2 validation failed: no competitors entered.", "WARN")
        return

    log_event(f"CI Step 2 completed with {len(competitors[:8])} competitors.")
    st.session_state.ci_config = {
        "own_brand": {
            "name": st.session_state.ci_own_brand_name.strip(),
            "website": st.session_state.ci_own_brand_website.strip(),
            "positioning": st.session_state.ci_own_brand_positioning.strip(),
        },
        "competitors": competitors[:8],
        "watch_phrases": [row.strip() for row in watch_phrases.splitlines() if row.strip()],
        "focus_areas": focus_areas,
        "cadence": "weekly",
        "use_hn_signals": True,
        "use_meta_ads": False,
    }
    st.session_state.ci_stage = "analysis"
    st.rerun()


def ci_analysis_step() -> None:
    render_steps(
        st.session_state.ci_stage,
        [("brand", "Your Brand"), ("competitors", "Your Competitors"), ("analysis", "Analysis"), ("digest", "Dashboard")],
    )
    st.subheader("Competitor Intelligence • Step 3: Analysis")
    cadence = st.selectbox("Cadence", ["Weekly", "Run Manually"])
    opt_col1, opt_col2 = st.columns(2)
    with opt_col1:
        use_hn_signals = st.checkbox("Use Hacker News signals (optional)", value=True)
    with opt_col2:
        use_meta_ads = st.checkbox("Use Meta Ad Library (optional, token in .env)", value=False)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Step 3 → Step 2: Edit Competitors", use_container_width=True):
            log_event("CI moved from Step 3 back to Step 2.")
            st.session_state.ci_stage = "competitors"
            st.rerun()
    with c2:
        if st.button("Step 3 → Step 4: Run Analysis", use_container_width=True):
            st.session_state.ci_config["cadence"] = cadence.lower()
            st.session_state.ci_config["use_hn_signals"] = use_hn_signals
            st.session_state.ci_config["use_meta_ads"] = use_meta_ads
            log_event(
                f"CI Step 3 started analysis for {len(st.session_state.ci_config['competitors'])} competitors "
                f"(HN={use_hn_signals}, Meta={use_meta_ads})."
            )
            st.session_state.ci_stage = "running"
            st.rerun()


def ci_running_screen() -> None:
    config = st.session_state.ci_config
    st.subheader("Competitor Intelligence Agent • Running")

    status = st.empty()
    progress = st.progress(0)
    log_box = st.empty()
    logs: list[str] = []

    def on_progress(current: int, total: int, step: str) -> None:
        progress.progress(int((current / total) * 100))
        status.markdown(f"Processing competitor {current}/{total}")
        logs.append(step)
        log_box.code("\n".join(logs[-10:]))
        log_event(f"CI progress {current}/{total}: {step}")

    context_id = st.session_state.ci_config["own_brand"]["name"].lower().replace(" ", "_")
    start_dev_log_run("ci", context_id)
    log_event("CI runtime started.", "INFO")
    try:
        log_event("CI run initiated.")
        result = run_competitor_intelligence(
            own_brand=config["own_brand"],
            competitors=config["competitors"],
            use_hn_signals=config["use_hn_signals"],
            use_meta_ads=config["use_meta_ads"],
            progress_callback=on_progress,
            debug_callback=log_event if st.session_state.verbose_mode else None,
        )
    except Exception as exc:
        st.error(f"Competitor Intelligence run failed: {exc}")
        log_event(f"CI run failed: {exc}", "ERROR")
        if st.button("Back"):
            st.session_state.ci_stage = "analysis"
            st.rerun()
        return

    payload = result.to_dict()
    output_path = save_audit_payload(f"ci_{result.run_id}", payload)
    append_audit_log(
        {
            "agent": "competitor_intelligence",
            "run_id": result.run_id,
            "brand_name": config["own_brand"]["name"],
            "competitors": len(config["competitors"]),
            "runtime_seconds": result.runtime_seconds,
            "result_file": str(output_path),
            "hn_enabled": config["use_hn_signals"],
            "meta_enabled": config["use_meta_ads"],
        }
    )

    st.session_state.ci_result = result
    log_event(
        f"CI run complete: competitors={len(result.competitors)}, runtime={result.runtime_seconds}s, "
        f"digest_items={len(result.digest.get('recommended_actions', []))}."
    )
    st.session_state.ci_stage = "digest"
    st.rerun()


def ci_digest_screen() -> None:
    result = st.session_state.ci_result
    digest = result.digest

    render_steps(
        "digest",
        [("brand", "Your Brand"), ("competitors", "Your Competitors"), ("analysis", "Analysis"), ("digest", "Dashboard")],
    )
    st.subheader("Competitor Intelligence Agent • Weekly Digest")
    st.caption(
        f"Week of {datetime.now().strftime('%Y-%m-%d')} • "
        f"{len(result.competitors)} competitors monitored • Run time: {result.runtime_seconds}s"
    )
    with st.expander("Dashboard Metrics Explained", expanded=False):
        st.markdown(
            "- **CVS (Competitive Velocity Score)**: 0-100 index of how fast a competitor is moving (site changes, ad activity, public signals).\n"
            "- **CVS Category**: Dormant, Steady, Active, Aggressive, Sprint based on CVS range.\n"
            "- **Threat Level**: Low/Medium/High risk to your current market narrative.\n"
            "- **Speed of Movement**: How quickly that competitor appears to be iterating this cycle.\n"
            "- **Recommended Actions**: Prioritized responses your marketing team should execute next."
        )

    st.markdown("### Executive Summary")
    for bullet in digest.get("executive_summary", []):
        st.markdown(f"- {bullet}")

    st.markdown("### Competitor Scorecards")
    cols = st.columns(3)
    for idx, item in enumerate(result.competitors):
        with cols[idx % 3]:
            with st.container(border=True):
                logo_url = _logo_from_website(item.get("website", ""), item.get("competitor_name", "Brand"))
                st.image(logo_url, width=36)
                st.markdown(f"**{item['competitor_name']}**")
                st.write(f"CVS: {item['cvs_score']} ({item['cvs_category'].upper()})")
                st.write(f"Threat: {item['threat_level'].upper()}")
                st.write(f"Speed: {item.get('speed_of_movement', 'moderate').upper()}")
                st.caption(build_marketing_summary(item))

    st.markdown("### Deep Dives")
    for item in result.competitors:
        if item["cvs_score"] <= 40:
            continue
        with st.expander(f"{item['competitor_name']} • CVS {item['cvs_score']}"):
            st.write(f"What changed: {item.get('what_changed', '-')}")
            st.write(f"Strategic interpretation: {item.get('strategic_interpretation', '-')}")
            st.write(f"Marketing summary: {build_marketing_summary(item)}")
            st.write(f"Recommended response: {item.get('recommended_response', '-')}")
            if item.get("meta_ads", {}).get("enabled"):
                st.write("Top ad themes:", ", ".join(item.get("meta_ads", {}).get("top_ad_themes", [])) or "-")

    st.markdown("### Recommended Actions")
    for idx, action in enumerate(digest.get("recommended_actions", []), start=1):
        with st.container(border=True):
            st.markdown(f"**{idx}. {action.get('action', '-') }**")
            st.write(f"Urgency: {action.get('urgency', 'this_week')}")
            st.write(f"Rationale: {action.get('rationale', '-')}")

    st.markdown("### Competitor vs Your Brand Dashboard")
    own_brand_name = result.own_brand.get("name", "Your Brand")
    comp_rows = []
    for item in result.competitors:
        cvs = float(item.get("cvs_score", 0))
        if cvs >= 70:
            action_priority = "Act Now"
        elif cvs >= 45:
            action_priority = "Plan This Week"
        else:
            action_priority = "Monitor"
        comp_rows.append(
            {
                "Your Brand": own_brand_name,
                "Competitor": item.get("competitor_name", "-"),
                "CVS": cvs,
                "CVS Category": str(item.get("cvs_category", "-")).title(),
                "Threat": str(item.get("threat_level", "-")).upper(),
                "Speed": str(item.get("speed_of_movement", "-")).upper(),
                "Marketing Signal": (
                    item.get("strategic_interpretation", "")
                    or item.get("what_changed", "")
                    or "-"
                ),
                "Recommended Counter": item.get("recommended_response", "-"),
                "Action Priority": action_priority,
            }
        )

    if comp_rows:
        comp_df = pd.DataFrame(comp_rows)
        st.dataframe(
            comp_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "CVS": st.column_config.NumberColumn(
                    "CVS",
                    format="%.2f",
                    help="Competitive Velocity Score (0-100). Higher means faster and stronger market movement.",
                ),
                "Marketing Signal": st.column_config.TextColumn(
                    "Marketing Signal",
                    help="Primary strategic takeaway for positioning and campaign planning.",
                ),
                "Recommended Counter": st.column_config.TextColumn(
                    "Recommended Counter",
                    help="Suggested response your marketing team should execute.",
                ),
                "Action Priority": st.column_config.TextColumn(
                    "Action Priority",
                    help="Execution urgency based on velocity and threat.",
                ),
            },
        )

        act_now = sum(1 for row in comp_rows if row["Action Priority"] == "Act Now")
        plan_week = sum(1 for row in comp_rows if row["Action Priority"] == "Plan This Week")
        monitor = sum(1 for row in comp_rows if row["Action Priority"] == "Monitor")
        p1, p2, p3 = st.columns(3)
        p1.metric("Act Now Competitors", act_now)
        p2.metric("Plan This Week", plan_week)
        p3.metric("Monitor", monitor)
    else:
        st.info("No competitor comparison data available yet.")

    st.markdown("## 📊 Generic Competitor Intelligence Dashboard")
    generic = build_generic_ci_dashboard(result)
    if generic:
        st.markdown("### 1. Executive Summary")
        e1, e2, e3 = st.columns(3)
        e1.metric("Market Position", generic["market_position"])
        e2.metric("Threat Level Trend", generic["threat_trend"])
        e3.metric("Key Competitor", generic["key_competitor"])
        e4, e5, e6 = st.columns(3)
        e4.metric("Fastest Growing Competitor", generic["fastest_growing_competitor"])
        e5.metric("Market Share Trend", generic["market_share_trend"])
        e6.metric("Your Brand", generic["own_brand"])

        st.markdown("### 2. Market Share Comparison")
        st.dataframe(pd.DataFrame(generic["market_table"]), use_container_width=True, hide_index=True)
        st.caption("Insight: You may still lead in scale, but fast movers can gain share through sharper positioning.")

        st.markdown("### 3. Pricing / Value Positioning Intelligence")
        st.dataframe(pd.DataFrame(generic["pricing_table"]), use_container_width=True, hide_index=True)
        st.caption("Insight: Pricing bands indicate positioning pressure and premium/value strategy shifts.")

        st.markdown("### 4. Marketing & Campaign Intelligence")
        st.dataframe(pd.DataFrame(generic["campaign_table"]), use_container_width=True, hide_index=True)
        st.caption("Insight: Campaign signals reveal how competitors are reframing demand and category narrative.")

        st.markdown("### 5. Digital & Engagement Performance")
        st.dataframe(pd.DataFrame(generic["digital_table"]), use_container_width=True, hide_index=True)
        st.caption("Insight: Scale and engagement depth can diverge; both impact conversion momentum.")

        st.markdown("### 6. Product Innovation Tracker")
        for line in generic["innovation_lines"]:
            st.markdown(f"- {line}")

        st.markdown("### 7. SWOT Snapshot (Your Brand)")
        st.markdown(
            "- **Strengths**: Brand visibility and current category presence.\n"
            "- **Weaknesses**: Slower movement in one or more competitor pressure areas.\n"
            "- **Opportunities**: Counter-positioning content, offer clarity, proof-led messaging.\n"
            "- **Threats**: Fast-moving competitors with sharper campaign or pricing signals."
        )

        st.markdown("### 8. Alerts & Signals")
        for alert in generic["alerts"]:
            st.markdown(f"- {alert}")
    else:
        st.info("Insufficient data to render generic competitor dashboard.")

    report_text = json.dumps(digest, indent=2)
    st.text_area("Copy Digest JSON", value=report_text, height=260)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Restart CI Wizard", use_container_width=True):
            st.session_state.ci_result = None
            st.session_state.ci_config = None
            st.session_state.ci_stage = "brand"
            st.rerun()
    with col2:
        if st.button("Step 4: Back to Home", use_container_width=True):
            st.session_state.nav_page = "Home"
            st.query_params["page"] = "Home"
            st.rerun()


def competitor_agent_page() -> None:
    stage = st.session_state.ci_stage
    if stage == "brand":
        ci_brand_step()
    elif stage == "competitors":
        ci_competitors_step()
    elif stage == "analysis":
        ci_analysis_step()
    elif stage == "running":
        ci_running_screen()
    elif stage == "digest":
        ci_digest_screen()


def history_page() -> None:
    st.subheader("Run History")
    history = load_audit_history()
    if not history:
        st.info("No runs saved yet.")
        return

    rows = []
    for item in history:
        if "score" in item:
            context = item.get("context", {})
            score = item.get("score", {})
            rows.append(
                {
                    "Agent": "GEO",
                    "ID": context.get("audit_id", "-"),
                    "Brand": context.get("brand_name", "-"),
                    "Primary Score": score.get("visibility_score", 0),
                    "Runtime (s)": score.get("runtime_seconds", 0),
                }
            )
        elif item.get("digest"):
            rows.append(
                {
                    "Agent": "Competitor Intelligence",
                    "ID": item.get("run_id", "-"),
                    "Brand": item.get("own_brand", {}).get("name", "-"),
                    "Primary Score": len(item.get("competitors", [])),
                    "Runtime (s)": item.get("runtime_seconds", 0),
                }
            )

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


init_state()
apply_openrouter_style()
sync_nav_from_query_params()
st.query_params["page"] = st.session_state.nav_page
render_sticky_navigation()
render_header()
if not st.session_state.app_logs:
    log_event(f"LOGGER_INIT dev_log_dir={DEV_LOG_DIR} xf_file={TRACE_MIRROR_FILE}")

if st.session_state.nav_page == "History":
    history_page()
elif st.session_state.nav_page == "GEO Agent":
    geo_agent_page()
elif st.session_state.nav_page == "Competitor Intelligence Agent":
    competitor_agent_page()
else:
    home_page()

render_logs_panel()
render_footer()
