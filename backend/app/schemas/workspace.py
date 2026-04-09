from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class BrandAsset(BaseModel):
    name: str
    kind: str
    size_bytes: int
    content_type: str


class BrandWorkspace(BaseModel):
    workspace_id: str
    workspace_name: str
    brand_name: str
    website: str
    industry: str
    category: str | None = None
    geography: str | None = None
    positioning: str | None = None
    additional_details: str | None = None
    brand_summary: str | None = None
    brand_analysis: dict[str, str] = Field(default_factory=dict)
    key_pages: list[str] = Field(default_factory=list)
    assets: list[BrandAsset] = Field(default_factory=list)
    updated_at: datetime


class UpsertBrandWorkspace(BaseModel):
    workspace_id: str
    workspace_name: str | None = None
    brand_name: str
    website: str
    industry: str
    category: str | None = None
    geography: str | None = None
    positioning: str | None = None
    additional_details: str | None = None
    brand_summary: str | None = None
    brand_analysis: dict[str, str] = Field(default_factory=dict)
    key_pages: list[str] = Field(default_factory=list)
    assets: list[BrandAsset] = Field(default_factory=list)


class AddBrandAsset(BaseModel):
    name: str
    kind: str
    size_bytes: int
    content_type: str
