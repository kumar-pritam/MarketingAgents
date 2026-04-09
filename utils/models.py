from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class QueryType(str, Enum):
    INFORMATIONAL = "informational"
    COMPARATIVE = "comparative"
    EVALUATIVE = "evaluative"
    RANKING = "ranking"
    AUTHORITY = "authority"


class MentionPosition(str, Enum):
    FIRST = "first"
    SECOND = "second"
    BURIED = "buried"
    ABSENT = "absent"


class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"


@dataclass(slots=True)
class BrandContext:
    brand_name: str
    category: str
    industry: str
    region: str
    competitors: list[str]
    keywords: list[str]
    audit_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class QueryItem:
    query_id: str
    text: str
    type: QueryType
    target_topic: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["type"] = self.type.value
        return data


@dataclass(slots=True)
class LLMResponse:
    query_id: str
    raw_response: str
    model: str
    tokens_used: int
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CompetitorMention:
    name: str
    position: MentionPosition
    sentiment: Sentiment

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["position"] = self.position.value
        data["sentiment"] = self.sentiment.value
        return data


@dataclass(slots=True)
class ParsedResult:
    query_id: str
    brand_mentioned: bool
    brand_position: MentionPosition
    brand_sentiment: Sentiment
    brand_context: str
    competitors_mentioned: list[CompetitorMention]
    source_signal: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "brand_mentioned": self.brand_mentioned,
            "brand_position": self.brand_position.value,
            "brand_sentiment": self.brand_sentiment.value,
            "brand_context": self.brand_context,
            "competitors_mentioned": [item.to_dict() for item in self.competitors_mentioned],
            "source_signal": self.source_signal,
        }


@dataclass(slots=True)
class CompetitorScore:
    ai_sov_pct: float
    visibility_score: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class GapItem:
    topic: str
    gap_score: float
    dominant_competitor: str
    query_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AuditScore:
    audit_id: str
    brand_name: str
    ai_sov_pct: float
    visibility_score: float
    competitor_scores: dict[str, CompetitorScore]
    gaps: list[GapItem]
    total_queries: int
    tokens_used: int
    runtime_seconds: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "brand_name": self.brand_name,
            "ai_sov_pct": self.ai_sov_pct,
            "visibility_score": self.visibility_score,
            "competitor_scores": {
                name: score.to_dict() for name, score in self.competitor_scores.items()
            },
            "gaps": [gap.to_dict() for gap in self.gaps],
            "total_queries": self.total_queries,
            "tokens_used": self.tokens_used,
            "runtime_seconds": self.runtime_seconds,
        }
