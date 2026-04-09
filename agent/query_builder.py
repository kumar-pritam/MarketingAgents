from __future__ import annotations

from itertools import cycle

from utils.helpers import dedupe_keep_order
from utils.models import BrandContext, QueryItem, QueryType

DEFAULT_QUERY_COUNT = 10
MIN_QUERY_COUNT = 3
MAX_QUERY_COUNT = 30


def _topic_pool(context: BrandContext) -> list[str]:
    base_topics = [context.category, *context.keywords]
    return dedupe_keep_order(base_topics) or [context.category]


def build_queries(context: BrandContext, total_queries: int = DEFAULT_QUERY_COUNT) -> list[QueryItem]:
    total_queries = max(MIN_QUERY_COUNT, min(total_queries, MAX_QUERY_COUNT))
    topics = _topic_pool(context)
    competitors = context.competitors
    region = context.region

    query_templates: dict[QueryType, list[str]] = {
        QueryType.INFORMATIONAL: [
            "Best {category} for {topic}",
            "How to choose {category} for {topic}",
            "What should buyers evaluate before selecting {category} for {topic}",
        ],
        QueryType.COMPARATIVE: [
            "Compare {brand} vs {competitor} for {topic}",
            "{brand} or {competitor}: which is better for {topic}",
            "{brand} alternatives for {topic}",
        ],
        QueryType.EVALUATIVE: [
            "Which {category} is most trusted for {topic}",
            "What is the most reliable {category} for {topic}",
            "What are the pros and cons of leading {category} options for {topic}",
        ],
        QueryType.RANKING: [
            "Top {category} providers in {region} for {topic}",
            "Top-rated {category} companies in {region}",
            "Top 10 {category} platforms for {topic}",
        ],
        QueryType.AUTHORITY: [
            "What do experts recommend for {topic} in {category}",
            "Which {category} brands are most referenced by analysts for {topic}",
            "What are industry best practices for {topic} in {category}",
        ],
    }

    sequence = [
        QueryType.INFORMATIONAL,
        QueryType.COMPARATIVE,
        QueryType.EVALUATIVE,
        QueryType.RANKING,
        QueryType.AUTHORITY,
    ]

    topic_cycle = cycle(topics)
    competitor_cycle = cycle(competitors or ["competitor"])
    type_cycle = cycle(sequence)

    generated: list[QueryItem] = []

    for idx in range(total_queries):
        query_type = next(type_cycle)
        topic = next(topic_cycle)
        competitor = next(competitor_cycle)
        templates = query_templates[query_type]
        template = templates[idx % len(templates)]
        text = template.format(
            category=context.category,
            brand=context.brand_name,
            competitor=competitor,
            topic=topic,
            region=region,
        )
        generated.append(
            QueryItem(
                query_id=f"q_{idx + 1:03d}",
                text=text,
                type=query_type,
                target_topic=topic,
            )
        )

    return generated
