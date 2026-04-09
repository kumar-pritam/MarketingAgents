from __future__ import annotations

import difflib
import re

from utils.helpers import normalize_text
from utils.models import (
    BrandContext,
    CompetitorMention,
    LLMResponse,
    MentionPosition,
    ParsedResult,
    Sentiment,
)

POSITIVE_MARKERS = ["best", "trusted", "leading", "strong", "recommended", "reliable"]
NEGATIVE_MARKERS = ["weak", "poor", "expensive", "limited", "not ideal", "complaint"]
MIXED_MARKERS = ["however", "but", "trade-off", "depends", "mixed"]


class ResponseParser:
    def __init__(self, context: BrandContext) -> None:
        self.context = context

    @staticmethod
    def _normalize_for_match(text: str) -> str:
        lowered = normalize_text(text).replace("&", " and ")
        lowered = re.sub(r"[^a-z0-9\s]", " ", lowered)
        return re.sub(r"\s+", " ", lowered).strip()

    @staticmethod
    def _collapsed(text: str) -> str:
        return re.sub(r"\s+", "", text)

    def _name_aliases(self, name: str) -> list[str]:
        normalized = self._normalize_for_match(name)
        aliases = {normalized}
        aliases.add(normalized.replace(" and ", " "))
        if normalized.startswith("the "):
            aliases.add(normalized.replace("the ", "", 1))
        if normalized.endswith(" co"):
            aliases.add(normalized + "mpany")
        if normalized.endswith(" company"):
            aliases.add(normalized.replace(" company", " co"))
        return [alias.strip() for alias in aliases if alias.strip()]

    def _find_fuzzy_index(self, text_norm: str, alias: str) -> int | None:
        tokens = text_norm.split()
        alias_tokens = alias.split()
        if not tokens or not alias_tokens:
            return None

        target = " ".join(alias_tokens)
        min_window = max(1, len(alias_tokens) - 1)
        max_window = min(len(tokens), len(alias_tokens) + 1)

        best_ratio = 0.0
        best_phrase = ""
        for window in range(min_window, max_window + 1):
            for idx in range(0, len(tokens) - window + 1):
                phrase = " ".join(tokens[idx : idx + window])
                ratio = difflib.SequenceMatcher(None, phrase, target).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_phrase = phrase

        if best_ratio >= 0.88 and best_phrase:
            return text_norm.find(best_phrase)
        return None

    def _find_position(self, text: str, name: str) -> MentionPosition:
        text_norm = self._normalize_for_match(text)
        text_collapsed = self._collapsed(text_norm)
        mentions: list[int] = []

        for alias in self._name_aliases(name):
            pattern = rf"\b{re.escape(alias)}\b"
            mentions.extend(match.start() for match in re.finditer(pattern, text_norm))

            alias_collapsed = self._collapsed(alias)
            collapsed_idx = text_collapsed.find(alias_collapsed)
            if collapsed_idx >= 0:
                approx_idx = int((collapsed_idx / max(len(text_collapsed), 1)) * len(text_norm))
                mentions.append(approx_idx)

            fuzzy_idx = self._find_fuzzy_index(text_norm, alias)
            if fuzzy_idx is not None:
                mentions.append(fuzzy_idx)

        if not mentions:
            return MentionPosition.ABSENT

        # Early mention in answer generally indicates stronger ranking intent.
        rank_index = min(mentions)
        if rank_index < 80:
            return MentionPosition.FIRST
        if rank_index < 220:
            return MentionPosition.SECOND
        return MentionPosition.BURIED

    def _sentiment(self, snippet: str) -> Sentiment:
        lowered = normalize_text(snippet)
        pos_hits = sum(1 for marker in POSITIVE_MARKERS if marker in lowered)
        neg_hits = sum(1 for marker in NEGATIVE_MARKERS if marker in lowered)
        mixed_hits = sum(1 for marker in MIXED_MARKERS if marker in lowered)

        if mixed_hits > 0 or (pos_hits > 0 and neg_hits > 0):
            return Sentiment.MIXED
        if pos_hits > neg_hits:
            return Sentiment.POSITIVE
        if neg_hits > pos_hits:
            return Sentiment.NEGATIVE
        return Sentiment.NEUTRAL

    def _brand_context(self, text: str, brand_mentioned: bool) -> str:
        if not brand_mentioned:
            return "absent"
        lowered = normalize_text(text)
        if "compare" in lowered or "vs" in lowered:
            return "compared"
        if "recommend" in lowered or "best" in lowered:
            return "recommended"
        if "critic" in lowered or "concern" in lowered:
            return "criticized"
        return "mentioned"

    def parse(self, response: LLMResponse) -> ParsedResult:
        text = response.raw_response or ""
        brand_position = self._find_position(text, self.context.brand_name)
        brand_mentioned = brand_position != MentionPosition.ABSENT
        brand_sentiment = self._sentiment(text)

        competitors: list[CompetitorMention] = []
        for competitor in self.context.competitors:
            position = self._find_position(text, competitor)
            if position == MentionPosition.ABSENT:
                continue
            competitors.append(
                CompetitorMention(
                    name=competitor,
                    position=position,
                    sentiment=self._sentiment(text),
                )
            )

        source_signal = bool(re.search(r"https?://|www\.|source:|according to", text, re.IGNORECASE))

        return ParsedResult(
            query_id=response.query_id,
            brand_mentioned=brand_mentioned,
            brand_position=brand_position,
            brand_sentiment=brand_sentiment,
            brand_context=self._brand_context(text, brand_mentioned),
            competitors_mentioned=competitors,
            source_signal=source_signal,
        )

    def batch_parse(self, responses: list[LLMResponse]) -> list[ParsedResult]:
        return [self.parse(response) for response in responses]
