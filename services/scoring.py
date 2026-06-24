from __future__ import annotations

from typing import Any

DEFAULT_WEIGHTS = {
    "learning": 0.18,
    "growth": 0.18,
    "compensation": 0.14,
    "stability": 0.12,
    "work_life_balance": 0.12,
    "brand": 0.08,
    "role_fit": 0.18,
    "risk": 0.10,
}

POSITIVE_SCORE_KEYS = [
    "learning",
    "growth",
    "compensation",
    "stability",
    "work_life_balance",
    "brand",
    "role_fit",
]


def total_score(data: dict[str, Any], weights: dict[str, float] | None = None) -> float:
    scores = data.get("scores", {})
    resolved_weights = dict(DEFAULT_WEIGHTS)
    if weights:
        resolved_weights.update(weights)

    positive = 0.0
    for key in POSITIVE_SCORE_KEYS:
        positive += (scores.get(key, 0) / 10.0) * resolved_weights.get(key, 0.0)

    risk_bonus = ((10.0 - scores.get("risk", 0)) / 10.0) * resolved_weights.get("risk", 0.0)
    total_weight = sum(resolved_weights.get(key, 0.0) for key in resolved_weights)
    if total_weight <= 0:
        return 0.0

    total = (positive + risk_bonus) / total_weight
    return round(total * 100, 1)


def rank_companies(entries: list[dict[str, Any]], weights: dict[str, float] | None = None) -> list[dict[str, Any]]:
    ranked = []
    for entry in entries:
        ranked.append(
            {
                **entry,
                "score": total_score(entry["analysis"], weights=weights),
            }
        )

    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked
