from __future__ import annotations

from collections import Counter, defaultdict
from time import perf_counter

from utils.models import (
    AuditScore,
    BrandContext,
    CompetitorScore,
    GapItem,
    MentionPosition,
    ParsedResult,
    QueryItem,
    Sentiment,
)

POSITION_POINTS = {
    MentionPosition.FIRST: 10,
    MentionPosition.SECOND: 7,
    MentionPosition.BURIED: 3,
    MentionPosition.ABSENT: 0,
}

SENTIMENT_POINTS = {
    Sentiment.POSITIVE: 10,
    Sentiment.NEUTRAL: 6,
    Sentiment.NEGATIVE: 2,
    Sentiment.MIXED: 4,
}

INTENT_WEIGHT = {
    "informational": 1.0,
    "comparative": 1.4,
    "evaluative": 1.3,
    "ranking": 1.2,
    "authority": 1.1,
}


def _ai_sov(mention_count: int, total_queries: int) -> float:
    if total_queries == 0:
        return 0.0
    return round((mention_count / total_queries) * 100, 2)


def _visibility(mention_rate: float, avg_position_score: float, avg_sentiment_score: float) -> float:
    score = (mention_rate * 0.4) + (avg_position_score * 0.3) + (avg_sentiment_score * 0.3)
    return round(score * 10, 2)


def score_audit(
    context: BrandContext,
    queries: list[QueryItem],
    parsed_results: list[ParsedResult],
    total_tokens: int,
    runtime_seconds: float,
) -> AuditScore:
    total_queries = len(parsed_results)

    brand_mentions = sum(1 for result in parsed_results if result.brand_mentioned)
    mention_rate_points = (brand_mentions / total_queries) * 10 if total_queries else 0

    avg_brand_position = (
        sum(POSITION_POINTS[result.brand_position] for result in parsed_results) / total_queries
        if total_queries
        else 0
    )
    avg_brand_sentiment = (
        sum(SENTIMENT_POINTS[result.brand_sentiment] for result in parsed_results) / total_queries
        if total_queries
        else 0
    )

    ai_sov_pct = _ai_sov(brand_mentions, total_queries)
    visibility_score = _visibility(mention_rate_points, avg_brand_position, avg_brand_sentiment)

    competitor_mention_map: dict[str, list[tuple[MentionPosition, Sentiment]]] = defaultdict(list)
    for result in parsed_results:
        for competitor in result.competitors_mentioned:
            competitor_mention_map[competitor.name].append((competitor.position, competitor.sentiment))

    competitor_scores: dict[str, CompetitorScore] = {}
    for competitor in context.competitors:
        mentions = competitor_mention_map.get(competitor, [])
        mention_count = len(mentions)
        mention_points = (mention_count / total_queries) * 10 if total_queries else 0
        avg_position = (
            sum(POSITION_POINTS[pos] for pos, _ in mentions) / mention_count if mention_count else 0
        )
        avg_sentiment = (
            sum(SENTIMENT_POINTS[sent] for _, sent in mentions) / mention_count if mention_count else 0
        )
        competitor_scores[competitor] = CompetitorScore(
            ai_sov_pct=_ai_sov(mention_count, total_queries),
            visibility_score=_visibility(mention_points, avg_position, avg_sentiment),
        )

    query_map = {query.query_id: query for query in queries}
    gap_tracker: dict[str, Counter[str]] = defaultdict(Counter)
    weighted_query_count: dict[str, float] = defaultdict(float)

    for result in parsed_results:
        query = query_map.get(result.query_id)
        if not query or result.brand_mentioned:
            continue

        topic = query.target_topic
        intent_weight = INTENT_WEIGHT.get(query.type.value, 1.0)
        weighted_query_count[topic] += intent_weight

        for competitor in result.competitors_mentioned:
            gap_tracker[topic][competitor.name] += 1

    gaps: list[GapItem] = []
    for topic, competitor_counter in gap_tracker.items():
        if not competitor_counter:
            continue
        dominant, freq = competitor_counter.most_common(1)[0]
        gap_score = round(freq * weighted_query_count[topic], 2)
        gaps.append(
            GapItem(
                topic=topic,
                gap_score=gap_score,
                dominant_competitor=dominant,
                query_count=int(weighted_query_count[topic]),
            )
        )

    gaps.sort(key=lambda item: item.gap_score, reverse=True)

    return AuditScore(
        audit_id=context.audit_id,
        brand_name=context.brand_name,
        ai_sov_pct=ai_sov_pct,
        visibility_score=visibility_score,
        competitor_scores=competitor_scores,
        gaps=gaps[:5],
        total_queries=total_queries,
        tokens_used=total_tokens,
        runtime_seconds=round(runtime_seconds, 2),
    )


def timed_score_audit(
    context: BrandContext,
    queries: list[QueryItem],
    parsed_results: list[ParsedResult],
    total_tokens: int,
) -> AuditScore:
    started = perf_counter()
    result = score_audit(context, queries, parsed_results, total_tokens, runtime_seconds=0)
    runtime = perf_counter() - started
    result.runtime_seconds = round(result.runtime_seconds + runtime, 2)
    return result
