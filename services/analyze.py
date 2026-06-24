from __future__ import annotations

import json
import os
import re
from pathlib import Path
from string import Template
from typing import Any

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "evaluation.txt"
DEFAULT_MODEL = "llama-3.3-70b-versatile"
SCORE_KEYS = [
    "learning",
    "growth",
    "compensation",
    "stability",
    "work_life_balance",
    "brand",
    "role_fit",
    "risk",
]


def _get_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set")
    return Groq(api_key=api_key)


def _load_prompt_template() -> Template:
    return Template(PROMPT_PATH.read_text(encoding="utf-8"))


def _strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = _strip_code_fences(text)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if match is None:
            raise ValueError("Model response did not contain valid JSON")
        return json.loads(match.group(0))


def _normalize_analysis(data: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(data)
    normalized.setdefault("summary", "")
    normalized.setdefault("role_fit_summary", "")
    normalized.setdefault("pros", [])
    normalized.setdefault("cons", [])
    normalized.setdefault("recommendation", "")
    normalized.setdefault("confidence", 0)
    normalized.setdefault("evidence", [])

    scores = normalized.get("scores") or {}
    for key in SCORE_KEYS:
        scores.setdefault(key, 0)
    normalized["scores"] = scores

    return normalized


def analyze_company(
    company_name: str,
    role: str,
    context: str,
    location: str | None = None,
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    client = _get_client()
    prompt = _load_prompt_template().safe_substitute(
        company_name=company_name,
        role=role,
        location=location or "N/A",
        context=context,
    )

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    result = response.choices[0].message.content or ""
    parsed = _extract_json(result)
    return _normalize_analysis(parsed)