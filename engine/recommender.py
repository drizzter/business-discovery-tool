"""AI-powered recommendation engine using OpenAI-compatible API."""
import json
from openai import OpenAI

import config
from models import Business, Recommendation


client = OpenAI(
    base_url=config.OPENAI_BASE_URL,
    api_key=config.OPENAI_API_KEY,
    timeout=120.0,
)

MAX_LISTINGS_FOR_AI = 10  # Cap input size for faster API responses


def get_recommendations(
    businesses: list[Business],
    criteria: str,
    top_n: int = 5,
    structured_criteria: dict = None,
) -> list[dict]:
    """
    Analyze businesses against user criteria using AI.
    Returns structured recommendation dicts with scorecards.
    """
    if not businesses:
        return []

    # Cap listings to avoid huge prompts
    # Sort by price (lowest first) to get most relevant subset
    sorted_biz = sorted(businesses, key=lambda b: b.raw_data.get("price_min", 999999))
    capped_biz = sorted_biz[:MAX_LISTINGS_FOR_AI]

    # Build concise business summaries
    biz_summaries = []
    for i, biz in enumerate(capped_biz):
        price = biz.price_range or "POA"
        summary = f"[{i}] {biz.name} | {biz.category} | {biz.location} | {price}"
        if biz.description:
            summary += f" | {biz.description[:100]}"
        biz_summaries.append(summary)

    listings_text = "\n".join(biz_summaries)

    # Market context (keep brief)
    cat_counts = {}
    prices_by_cat = {}
    for biz in capped_biz:
        cat_counts[biz.category] = cat_counts.get(biz.category, 0) + 1
        if biz.category not in prices_by_cat:
            prices_by_cat[biz.category] = []
        price = biz.raw_data.get("price_min", 0)
        if price:
            prices_by_cat[biz.category].append(price)

    market_lines = []
    for cat, prices in sorted(prices_by_cat.items(), key=lambda x: -len(x[1])):
        if prices:
            avg = sum(prices) / len(prices)
            market_lines.append(f"{cat}: avg ${avg:,.0f} ({len(prices)} listed)")
    market_context = "Market: " + "; ".join(market_lines) if market_lines else ""

    # Structured criteria
    criteria_parts = []
    if structured_criteria:
        for key, label in [("budget", "Budget"), ("location", "Location"), ("industry", "Industry"),
                           ("involvement", "Involvement"), ("risk", "Risk tolerance"), ("roi", "Target ROI")]:
            val = structured_criteria.get(key, "")
            if val:
                criteria_parts.append(f"{label}: {val}")
    buyer_profile = "Buyer: " + "; ".join(criteria_parts) if criteria_parts else ""

    prompt = f"""Analyze these Australian businesses for sale. Recommend the best {top_n}.

Criteria: {criteria}
{buyer_profile}
{market_context}

Listings:
{listings_text}

Return JSON array. Each entry: index, overall_score (0-100), price_score (0-10), location_score (0-10), market_score (0-10), risk_level ("Low"/"Medium"/"High"), reasoning (1-2 sentences), highlights (array 2-3), risks (array 1-2), questions (array 2-3 for seller), next_step (one action).
Return ONLY the JSON array."""

    models_to_try = ["smart", "smart-nothink"]

    for model in models_to_try:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000,
                extra_body={"chat_template_kwargs": {"enable_thinking": False}},
            )
            raw = response.choices[0].message.content.strip()

            # Parse JSON
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()

            results = json.loads(raw)

            recommendations = []
            for r in results:
                idx = r["index"]
                if 0 <= idx < len(capped_biz):
                    recommendations.append({
                        "business": capped_biz[idx],
                        "overall_score": r.get("overall_score", 50),
                        "price_score": r.get("price_score", 5),
                        "location_score": r.get("location_score", 5),
                        "market_score": r.get("market_score", 5),
                        "risk_level": r.get("risk_level", "Medium"),
                        "reasoning": r.get("reasoning", ""),
                        "risks": r.get("risks", []),
                        "questions": r.get("questions", []),
                        "next_step": r.get("next_step", ""),
                        "highlights": r.get("highlights", []),
                    })
            if recommendations:
                return recommendations

        except Exception as e:
            print(f"AI model '{model}' error: {e}")
            continue

    # Fallback
    print("All AI models failed, using fallback ranking")
    return [
        {
            "business": b,
            "overall_score": 50,
            "price_score": 5,
            "location_score": 5,
            "market_score": 5,
            "risk_level": "Unknown",
            "reasoning": f"Fallback ranking by price (${b.raw_data.get('price_min', 0):,.0f}). AI analysis unavailable.",
            "risks": [],
            "questions": [],
            "next_step": "Contact broker for details",
            "highlights": [],
        }
        for b in sorted_biz[:top_n]
    ]
