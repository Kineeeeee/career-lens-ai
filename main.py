from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from services.analyze import analyze_company
from services.scoring import rank_companies
from services.search import build_context, search_company

DATA_DIR = Path("data/analyses")
COMPARISON_DIR = DATA_DIR / "comparisons"


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "item"


def _parse_companies(raw_companies: list[str] | None) -> list[str]:
    if not raw_companies:
        response = input("Nhập danh sách công ty (phân tách bằng dấu phẩy): ").strip()
        companies = [item.strip() for item in response.split(",") if item.strip()]
        return companies

    companies: list[str] = []
    for raw in raw_companies:
        parts = [item.strip() for item in raw.split(",") if item.strip()]
        companies.extend(parts)
    return companies


def _prompt_if_missing(value: str | None, message: str) -> str:
    if value and value.strip():
        return value.strip()
    response = input(message).strip()
    if not response:
        raise SystemExit("Thiếu thông tin bắt buộc.")
    return response


def _save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _save_company_bundle(
    company: str,
    role: str,
    location: str | None,
    search_payload: dict[str, Any],
    analysis: dict[str, Any],
    score: float,
) -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bundle = {
        "company": company,
        "role": role,
        "location": location,
        "score": score,
        "search": search_payload,
        "analysis": analysis,
        "saved_at": timestamp,
    }
    file_name = f"{_slugify(company)}__{_slugify(role)}__{timestamp}.json"
    _save_json(DATA_DIR / file_name, bundle)


def _save_comparison_report(
    role: str,
    location: str | None,
    ranked_entries: list[dict[str, Any]],
) -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = {
        "role": role,
        "location": location,
        "rankings": [
            {
                "company": item["company"],
                "score": item["score"],
                "analysis": item["analysis"],
            }
            for item in ranked_entries
        ],
        "saved_at": timestamp,
    }
    file_name = f"comparison__{_slugify(role)}__{timestamp}.json"
    _save_json(COMPARISON_DIR / file_name, report)


def _print_summary(ranked_entries: list[dict[str, Any]]) -> None:
    print("\n=== COMPANY RANKINGS ===\n")
    for index, item in enumerate(ranked_entries, start=1):
        analysis = item["analysis"]
        summary = analysis.get("summary", "")
        print(f"{index}. {item['company']} ({item['score']}/100)")
        if summary:
            print(f"   - {summary}")
        recommendation = analysis.get("recommendation", "")
        if recommendation:
            print(f"   - Recommend: {recommendation}")
        print()


def run() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze and compare companies for a target role."
    )
    parser.add_argument(
        "--companies",
        nargs="+",
        help="List of companies, e.g. --companies OpenAI Anthropic \"Google DeepMind\"",
    )
    parser.add_argument(
        "--role",
        help="Target role, e.g. Backend Engineer or Product Manager",
    )
    parser.add_argument(
        "--location",
        help="Optional target location for the comparison",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=4,
        help="Maximum search results per query",
    )
    args = parser.parse_args()

    companies = _parse_companies(args.companies)
    if not companies:
        raise SystemExit("Bạn cần cung cấp ít nhất 1 công ty.")

    role = _prompt_if_missing(args.role, "Nhập vị trí mong muốn: ")
    location = args.location.strip() if args.location else None

    entries: list[dict[str, Any]] = []

    for company in companies:
        print(f"\nAnalyzing {company}...\n")
        search_payload = search_company(
            company_name=company,
            role=role,
            location=location,
            max_results_per_query=args.max_results,
        )
        context = build_context(search_payload)
        analysis = analyze_company(
            company_name=company,
            role=role,
            context=context,
            location=location,
        )
        entries.append(
            {
                "company": company,
                "search": search_payload,
                "analysis": analysis,
            }
        )
        print("Done.")

    ranked_entries = rank_companies(entries)

    for item in ranked_entries:
        _save_company_bundle(
            company=item["company"],
            role=role,
            location=location,
            search_payload=item["search"],
            analysis=item["analysis"],
            score=item["score"],
        )

    _save_comparison_report(role, location, ranked_entries)
    _print_summary(ranked_entries)


if __name__ == "__main__":
    run()
