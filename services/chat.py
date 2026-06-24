"""Advanced chat interface with RAG for Career Lens AI.

Provides conversational interface with follow-up questions and context awareness.
"""

from __future__ import annotations

import json
from typing import Any

from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()


def _get_client() -> Groq:
    """Get Groq client."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set")
    return Groq(api_key=api_key)


def create_rag_prompt(
    user_question: str,
    retrieved_context: str,
    previous_analyses: list[dict[str, Any]] | None = None,
) -> str:
    """Create a prompt that incorporates RAG context.

    Args:
        user_question: The user's question
        retrieved_context: Context retrieved from RAG database
        previous_analyses: Previous company analyses for context

    Returns:
        Formatted prompt for LLM
    """
    context_section = ""

    if retrieved_context:
        context_section = f"""
## Previous Context from Database
{retrieved_context}

"""

    previous_section = ""
    if previous_analyses:
        previous_section = f"""
## Previously Analyzed Companies
{json.dumps(previous_analyses, indent=2, ensure_ascii=False)}

"""

    prompt = f"""You are Career Lens AI, an expert assistant for evaluating companies for job roles.

{context_section}{previous_section}

User Question: {user_question}

Provide a helpful, professional response based on the available context and previous analyses.
If relevant previous analyses exist, reference them and explain how they inform your answer.
Be specific and evidence-based in your recommendations.
"""

    return prompt


def chat_with_context(
    user_message: str,
    chat_history: list[dict[str, str]] | None = None,
    rag_context: str = "",
    previous_analyses: list[dict[str, Any]] | None = None,
    model: str = "llama-3.3-70b-versatile",
    temperature: float = 0.7,
) -> str:
    """Send a message with RAG context to Groq.

    Args:
        user_message: User's question/message
        chat_history: Previous messages in conversation
        rag_context: Context retrieved from RAG database
        previous_analyses: Previous company analyses
        model: LLM model to use
        temperature: Model temperature (0-1)

    Returns:
        Assistant's response
    """
    client = _get_client()

    # Build system message with RAG context
    system_message = """You are Career Lens AI, an expert assistant for evaluating companies for job roles.

Your capabilities:
- Compare multiple companies for specific job roles
- Provide role-aware scoring and recommendations
- Track analysis history and provide follow-up insights
- Give evidence-based recommendations with sources

When responding:
1. Be specific and factual
2. Reference previous analyses when relevant
3. Provide balanced pros and cons
4. Consider the user's target role
5. Suggest next steps if appropriate

"""

    if rag_context:
        system_message += f"\n## Database Context\n{rag_context}\n"

    if previous_analyses:
        system_message += f"\n## Previous Analyses\n{json.dumps(previous_analyses[:2], indent=2, ensure_ascii=False)}\n"

    # Build messages
    messages = [{"role": "user", "content": user_message}]

    if chat_history:
        # Insert history before current message
        messages = chat_history + messages

    # Call Groq
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        system=system_message,
        temperature=temperature,
        max_tokens=1000,
    )

    return response.choices[0].message.content


def generate_follow_up_questions(
    analysis_data: dict[str, Any],
    company_name: str,
    role: str,
) -> list[str]:
    """Generate suggested follow-up questions based on analysis.

    Args:
        analysis_data: Company analysis data
        company_name: Name of analyzed company
        role: Target role

    Returns:
        List of suggested follow-up questions
    """
    client = _get_client()

    analysis_json = json.dumps(analysis_data, indent=2, ensure_ascii=False)

    prompt = f"""Based on this analysis of {company_name} for role {role}, generate 3-4 insightful follow-up questions that would help the user make a better decision.

Analysis:
{analysis_json}

Format your response as a JSON array of strings, like:
["question 1", "question 2", "question 3"]

Only return the JSON array, no other text."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=500,
    )

    try:
        content = response.choices[0].message.content.strip()
        # Extract JSON array
        if "[" in content and "]" in content:
            json_str = content[content.index("["):content.rindex("]") + 1]
            questions = json.loads(json_str)
            return questions[:4]
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback questions
    return [
        f"How does {company_name}'s compensation compare to other companies in this space?",
        f"What are the typical career progression paths at {company_name}?",
        f"How is {company_name}'s work-life balance for {role} positions?",
    ]


def generate_comparison_insights(
    ranked_analyses: list[dict[str, Any]],
    role: str,
) -> str:
    """Generate insights about the comparison.

    Args:
        ranked_analyses: List of ranked company analyses
        role: Target role

    Returns:
        Text insights about the comparison
    """
    client = _get_client()

    companies_summary = json.dumps(
        [
            {
                "company": a["company"],
                "score": a["score"],
                "summary": a.get("analysis", {}).get("summary", ""),
            }
            for a in ranked_analyses
        ],
        indent=2,
        ensure_ascii=False,
    )

    prompt = f"""Analyze this company comparison for role: {role}

{companies_summary}

Provide 2-3 key insights about:
1. Which company is best suited and why
2. Any surprising findings in the comparison
3. Key decision factors the user should consider

Be concise and actionable."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=500,
    )

    return response.choices[0].message.content


def answer_specific_question(
    question: str,
    analysis_data: dict[str, Any],
    company_name: str,
) -> str:
    """Answer a specific question about a company based on its analysis.

    Args:
        question: Specific question about the company
        analysis_data: Company analysis data
        company_name: Name of company

    Returns:
        Answer to the question
    """
    client = _get_client()

    analysis_json = json.dumps(analysis_data, indent=2, ensure_ascii=False)

    prompt = f"""Based on this analysis of {company_name}, answer the following question:

Question: {question}

Analysis:
{analysis_json}

Provide a direct, evidence-based answer. If the information is in the analysis, cite it.
If not available, say so clearly."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=400,
    )

    return response.choices[0].message.content


def refine_recommendation(
    ranked_analyses: list[dict[str, Any]],
    user_preferences: dict[str, Any],
) -> dict[str, Any]:
    """Refine recommendation based on user preferences.

    Args:
        ranked_analyses: List of ranked company analyses
        user_preferences: User's stated preferences (e.g., prioritize learning over pay)

    Returns:
        Refined recommendation with explanation
    """
    client = _get_client()

    companies_data = json.dumps(ranked_analyses, indent=2, ensure_ascii=False)
    preferences_data = json.dumps(user_preferences, indent=2, ensure_ascii=False)

    prompt = f"""Given these company analyses and user preferences, provide a refined recommendation.

Companies:
{companies_data}

User Preferences:
{preferences_data}

Return a JSON object with:
{{
    "recommended_company": "company name",
    "reasoning": "explanation of choice",
    "alternative": "alternative option if primary doesn't work out",
    "key_factors": ["factor 1", "factor 2"],
    "risks_to_consider": ["risk 1", "risk 2"]
}}

Only return the JSON object."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=800,
    )

    try:
        content = response.choices[0].message.content.strip()
        if "{" in content and "}" in content:
            json_str = content[content.index("{"):content.rindex("}") + 1]
            return json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        pass

    return {
        "recommended_company": ranked_analyses[0]["company"] if ranked_analyses else "N/A",
        "reasoning": "Unable to generate detailed reasoning",
        "alternative": ranked_analyses[1]["company"] if len(ranked_analyses) > 1 else "N/A",
    }
