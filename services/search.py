from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()


def _get_client() -> TavilyClient:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY is not set")
    return TavilyClient(api_key=api_key)


def _build_queries(company_name: str, role: str | None, location: str | None) -> list[str]:
    role_clause = f" {role}" if role else ""
    location_clause = f" {location}" if location else ""

    return [
        f"{company_name}{role_clause}{location_clause} company overview culture reviews",
        f"{company_name}{role_clause}{location_clause} compensation benefits work life balance",
        f"{company_name}{role_clause}{location_clause} recent news growth layoffs funding",
    ]


def search_company(
    company_name: str,
    role: str | None = None,
    location: str | None = None,
    max_results_per_query: int = 4,
) -> dict[str, Any]:
    client = _get_client()
    queries = _build_queries(company_name, role, location)

    merged_results: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for query in queries:
        response = client.search(query=query, max_results=max_results_per_query)
        for item in response.get("results", []):
            url = item.get("url")
            if url and url in seen_urls:
                continue

            if url:
                seen_urls.add(url)

            merged_results.append(
                {
                    "title": item.get("title", ""),
                    "url": url or "",
                    "content": item.get("content", ""),
                    "score": item.get("score"),
                    "raw": item,
                    "query": query,
                }
            )

    return {
        "company": company_name,
        "role": role,
        "location": location,
        "queries": queries,
        "results": merged_results,
    }


def build_context(search_payload: dict[str, Any], limit: int = 8) -> str:
    lines: list[str] = []
    for index, item in enumerate(search_payload.get("results", [])[:limit], start=1):
        title = item.get("title") or "Untitled source"
        url = item.get("url") or "N/A"
        content = item.get("content") or ""
        lines.append(f"[{index}] {title}\nURL: {url}\nSnippet: {content}".strip())

    return "\n\n".join(lines)
