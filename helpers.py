"""Helper utilities for Career Lens AI.

Common functions for data processing, validation, and formatting.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def slugify(value: str) -> str:
    """Convert string to URL-friendly slug.

    Args:
        value: String to slugify

    Returns:
        Slugified string
    """
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "item"


def format_timestamp() -> str:
    """Get current timestamp in ISO format.

    Returns:
        ISO format timestamp
    """
    return datetime.now().isoformat()


def format_score_text(score: float, max_score: int = 100) -> str:
    """Format score as colored text.

    Args:
        score: Score value
        max_score: Maximum possible score

    Returns:
        Formatted score text
    """
    percentage = (score / max_score) * 100

    if percentage >= 75:
        return f"✅ {score:.1f}/{max_score} (Excellent)"
    elif percentage >= 50:
        return f"⚠️ {score:.1f}/{max_score} (Good)"
    else:
        return f"❌ {score:.1f}/{max_score} (Consider Carefully)"


def validate_companies(companies: list[str]) -> tuple[bool, str]:
    """Validate company list input.

    Args:
        companies: List of company names

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not companies:
        return False, "No companies provided"

    if len(companies) > 10:
        return False, "Too many companies (max 10)"

    for company in companies:
        if not company.strip():
            return False, "Empty company name"

    return True, ""


def validate_role(role: str) -> tuple[bool, str]:
    """Validate role input.

    Args:
        role: Target role

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not role or not role.strip():
        return False, "Role is required"

    if len(role) < 2:
        return False, "Role too short (min 2 characters)"

    if len(role) > 100:
        return False, "Role too long (max 100 characters)"

    return True, ""


def parse_companies_input(raw_input: str) -> list[str]:
    """Parse company input from various formats.

    Supports:
    - Comma-separated: "Google, Meta, Amazon"
    - Line-separated: "Google\nMeta\nAmazon"
    - Mixed separators

    Args:
        raw_input: Raw input string

    Returns:
        List of company names
    """
    companies = []

    # Try comma-separated first
    if "," in raw_input:
        companies = [c.strip() for c in raw_input.split(",")]
    else:
        # Try newline-separated
        companies = [c.strip() for c in raw_input.split("\n")]

    # Filter empty strings
    companies = [c for c in companies if c.strip()]

    return companies


def format_analysis_for_display(analysis: dict[str, Any]) -> str:
    """Format analysis data for display/printing.

    Args:
        analysis: Analysis data dictionary

    Returns:
        Formatted string representation
    """
    company = analysis.get("company", "Unknown")
    score = analysis.get("score", 0)
    analysis_data = analysis.get("analysis", {})

    lines = [
        f"Company: {company}",
        f"Score: {format_score_text(score)}",
    ]

    if summary := analysis_data.get("summary"):
        lines.append(f"Summary: {summary}")

    if pros := analysis_data.get("pros"):
        lines.append("Pros:")
        for pro in pros:
            lines.append(f"  • {pro}")

    if cons := analysis_data.get("cons"):
        lines.append("Cons:")
        for con in cons:
            lines.append(f"  • {con}")

    if recommendation := analysis_data.get("recommendation"):
        lines.append(f"Recommendation: {recommendation}")

    return "\n".join(lines)


def create_comparison_table(analyses: list[dict[str, Any]]) -> str:
    """Create ASCII table for company comparison.

    Args:
        analyses: List of analyzed companies

    Returns:
        ASCII table string
    """
    if not analyses:
        return "No analyses available"

    # Get headers
    headers = ["Rank", "Company", "Score", "Confidence"]
    if analyses[0].get("analysis", {}).get("scores"):
        headers.extend(analyses[0]["analysis"]["scores"].keys())

    # Prepare rows
    rows = []
    for idx, analysis in enumerate(analyses, 1):
        row = [
            str(idx),
            analysis.get("company", ""),
            f"{analysis.get('score', 0):.1f}",
            f"{analysis.get('analysis', {}).get('confidence', 0)}%",
        ]

        if scores := analysis.get("analysis", {}).get("scores"):
            row.extend([f"{v:.1f}" for v in scores.values()])

        rows.append(row)

    # Create table
    col_widths = [max(len(str(row[i])) for row in [headers] + rows) for i in range(len(headers))]

    # Format header
    header_line = " | ".join(
        str(headers[i]).ljust(col_widths[i]) for i in range(len(headers))
    )
    separator = "-+-".join("-" * w for w in col_widths)

    # Format rows
    data_lines = [
        " | ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(headers)))
        for row in rows
    ]

    return f"{header_line}\n{separator}\n" + "\n".join(data_lines)


def save_json_results(data: dict[str, Any], filename: str, directory: str = "data/results") -> Path:
    """Save analysis results as JSON file.

    Args:
        data: Data to save
        filename: Filename (without .json extension)
        directory: Directory to save in

    Returns:
        Path to saved file
    """
    output_dir = Path(directory)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not filename.endswith(".json"):
        filename += ".json"

    filepath = output_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return filepath


def extract_metrics_summary(analyses: list[dict[str, Any]]) -> dict[str, Any]:
    """Extract summary metrics from analyses.

    Args:
        analyses: List of analyses

    Returns:
        Summary statistics
    """
    if not analyses:
        return {}

    scores = [a.get("score", 0) for a in analyses]
    confidences = [a.get("analysis", {}).get("confidence", 0) for a in analyses]

    return {
        "total_companies": len(analyses),
        "avg_score": sum(scores) / len(scores) if scores else 0,
        "max_score": max(scores) if scores else 0,
        "min_score": min(scores) if scores else 0,
        "avg_confidence": sum(confidences) / len(confidences) if confidences else 0,
        "top_company": analyses[0].get("company") if analyses else None,
        "top_score": analyses[0].get("score") if analyses else 0,
    }


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def clean_text(text: str) -> str:
    """Clean and normalize text.

    Args:
        text: Text to clean

    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Remove special characters
    text = re.sub(r"[^\w\s\-.]", "", text)

    return text


def get_confidence_indicator(confidence: int) -> str:
    """Get visual indicator for confidence level.

    Args:
        confidence: Confidence percentage (0-100)

    Returns:
        Visual indicator
    """
    if confidence >= 90:
        return "🟢 Very High"
    elif confidence >= 75:
        return "🟡 High"
    elif confidence >= 50:
        return "🟠 Medium"
    else:
        return "🔴 Low"
