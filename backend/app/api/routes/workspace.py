from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import re

from app.core.security import is_valid_http_url, sanitize_text
from app.services.brand_enrichment import enrich_brand_profile, generate_brand_analysis
from app.schemas.workspace import AddBrandAsset, BrandAsset, BrandWorkspace, UpsertBrandWorkspace
from app.storage.repository import repo

router = APIRouter(prefix="/workspaces", tags=["workspace"])


class BrandEnrichmentRequest(BaseModel):
    brand_name: str


def _normalize_workspace(row: dict) -> dict:
    normalized = dict(row)
    normalized["workspace_name"] = normalized.get("workspace_name") or normalized.get("brand_name", "Workspace")
    normalized["additional_details"] = normalized.get("additional_details")
    normalized["category"] = normalized.get("category")
    normalized["geography"] = normalized.get("geography")
    normalized["brand_summary"] = normalized.get("brand_summary")
    normalized["brand_analysis"] = normalized.get("brand_analysis") or {}
    return normalized


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower()).strip()


@router.post("/enrich")
def enrich_brand(req: BrandEnrichmentRequest) -> dict:
    return enrich_brand_profile(req.brand_name)


class BrandAnalysisRequest(BaseModel):
    brand_name: str
    category: str
    geography: str


@router.post("/analyze")
def analyze_brand(req: BrandAnalysisRequest) -> dict:
    basic = enrich_brand_profile(req.brand_name)
    analysis = generate_brand_analysis(req.brand_name, req.category, req.geography)
    summary = (
        f'{req.brand_name} in {req.category} ({req.geography}) appears positioned as '
        f'{analysis.get("brand_positioning", "a differentiated player")[:120]}. '
        f'Primary risk: {analysis.get("brand_health_risks", "message inconsistency")[:120]}.'
    )
    return {
        **basic,
        "category": req.category,
        "geography": req.geography,
        "brand_summary": summary,
        "brand_analysis": analysis,
    }


@router.get("", response_model=list[BrandWorkspace])
def list_workspaces() -> list[BrandWorkspace]:
    rows = repo.list_workspaces()
    return [BrandWorkspace(**_normalize_workspace(row)) for row in rows]


@router.put("", response_model=BrandWorkspace)
def upsert_workspace(payload: UpsertBrandWorkspace) -> BrandWorkspace:
    cleaned = payload.model_dump()
    website = (cleaned.get("website") or "").strip()
    if not website:
        website = f'https://www.{_slugify(cleaned.get("brand_name", ""))}.com'
    if not is_valid_http_url(website):
        website = f'https://www.{_slugify(cleaned.get("brand_name", ""))}.com'
    cleaned["website"] = website

    valid_key_pages: list[str] = []
    for page in cleaned.get("key_pages", []):
        if isinstance(page, str) and is_valid_http_url(page):
            valid_key_pages.append(page)
    if not valid_key_pages:
        valid_key_pages = [website]
    cleaned["key_pages"] = valid_key_pages

    cleaned["brand_name"] = sanitize_text(cleaned["brand_name"], max_len=120)
    cleaned["workspace_name"] = sanitize_text(
        cleaned.get("workspace_name") or cleaned["brand_name"], max_len=120
    )
    cleaned["industry"] = sanitize_text(cleaned["industry"], max_len=120)
    if cleaned.get("category"):
        cleaned["category"] = sanitize_text(cleaned["category"], max_len=120)
    if cleaned.get("geography"):
        cleaned["geography"] = sanitize_text(cleaned["geography"], max_len=120)
    if cleaned.get("positioning"):
        cleaned["positioning"] = sanitize_text(cleaned["positioning"], max_len=2000)
    if cleaned.get("additional_details"):
        cleaned["additional_details"] = sanitize_text(cleaned["additional_details"], max_len=5000)
    if cleaned.get("brand_summary"):
        cleaned["brand_summary"] = sanitize_text(cleaned["brand_summary"], max_len=1000)
    raw_analysis = cleaned.get("brand_analysis") or {}
    if isinstance(raw_analysis, dict):
        cleaned["brand_analysis"] = {
            sanitize_text(str(k), max_len=80): sanitize_text(str(v), max_len=700)
            for k, v in raw_analysis.items()
            if str(k).strip()
        }
    else:
        cleaned["brand_analysis"] = {}
    saved = repo.upsert_workspace(cleaned)
    return BrandWorkspace(**_normalize_workspace(saved))


@router.get("/{workspace_id}", response_model=BrandWorkspace)
def get_workspace(workspace_id: str) -> BrandWorkspace:
    found = repo.get_workspace(workspace_id)
    if not found:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return BrandWorkspace(**_normalize_workspace(found))


@router.post("/{workspace_id}/assets", response_model=BrandWorkspace)
def add_workspace_asset(workspace_id: str, payload: AddBrandAsset) -> BrandWorkspace:
    try:
        updated = repo.add_workspace_asset(workspace_id, BrandAsset(**payload.model_dump()).model_dump())
    except KeyError:
        raise HTTPException(status_code=404, detail="Workspace not found") from None
    return BrandWorkspace(**_normalize_workspace(updated))
