"""RAG (Retrieval-Augmented Generation) service for Career Lens AI.

This module provides vector storage and retrieval functionality for company analyses.
Uses Chroma for vector storage and sentence-transformers for embeddings.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import chromadb

# Initialize Chroma with persistent storage
CHROMA_DB_PATH = Path("data/chroma_db")
CHROMA_DB_PATH.mkdir(parents=True, exist_ok=True)


def _get_chroma_client() -> chromadb.PersistentClient:
    """Get or create Chroma persistent client with new configuration."""
    return chromadb.PersistentClient(path=str(CHROMA_DB_PATH))


def _get_or_create_collection(client: chromadb.PersistentClient, collection_name: str) -> chromadb.Collection:
    """Get or create a Chroma collection for storing company data."""
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )


def store_company_analysis(
    company_name: str,
    role: str,
    analysis_data: dict[str, Any],
    evidence: list[dict[str, Any]] | None = None,
) -> str:
    """Store company analysis in vector database for retrieval.

    Args:
        company_name: Name of the company
        role: Target job role
        analysis_data: Full analysis dictionary containing scores and summary
        evidence: List of evidence/sources from analysis

    Returns:
        Document ID in the vector store
    """
    client = _get_chroma_client()
    collection = _get_or_create_collection(client, "company_analyses")

    # Prepare document content
    summary = analysis_data.get("summary", "")
    role_fit_summary = analysis_data.get("role_fit_summary", "")
    pros = ", ".join(analysis_data.get("pros", []))
    cons = ", ".join(analysis_data.get("cons", []))
    scores = analysis_data.get("scores", {})

    # Create comprehensive text for embedding
    document_text = f"""
    Company: {company_name}
    Role: {role}
    Summary: {summary}
    Role Fit: {role_fit_summary}
    Pros: {pros}
    Cons: {cons}
    Scores: {scores}
    Recommendation: {analysis_data.get('recommendation', '')}
    """

    # Create unique ID
    doc_id = f"{company_name.lower().replace(' ', '_')}_{role.lower().replace(' ', '_')}"

    # Create metadata
    metadata = {
        "company": company_name,
        "role": role,
        "score": str(analysis_data.get("score", 0)),
        "confidence": str(analysis_data.get("confidence", 0)),
    }

    # Add evidence to metadata
    if evidence:
        metadata["sources"] = ", ".join(
            [f"{e.get('source_title', 'Unknown')}" for e in evidence[:3]]
        )

    # Store in Chroma
    collection.add(
        ids=[doc_id],
        documents=[document_text],
        metadatas=[metadata],
    )

    return doc_id


def retrieve_similar_analyses(
    query: str,
    role: str | None = None,
    n_results: int = 3,
) -> list[dict[str, Any]]:
    """Retrieve similar company analyses from vector database.

    Args:
        query: Search query (company name, role criteria, etc.)
        role: Optional role to filter by
        n_results: Number of results to return

    Returns:
        List of similar analyses with metadata
    """
    client = _get_chroma_client()

    try:
        collection = client.get_collection("company_analyses")
    except Exception:
        # Collection doesn't exist yet
        return []

    # Add role to query for better filtering
    search_query = query
    if role:
        search_query = f"{query} {role}"

    # Query Chroma
    results = collection.query(
        query_texts=[search_query],
        n_results=n_results,
        where={"role": role} if role else None,
    )

    # Format results
    formatted_results = []
    if results and results["ids"]:
        for i, doc_id in enumerate(results["ids"][0]):
            formatted_results.append({
                "id": doc_id,
                "document": results["documents"][0][i] if results["documents"] else "",
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else 0,
            })

    return formatted_results


def get_all_analyses() -> list[dict[str, Any]]:
    """Get all stored company analyses.

    Returns:
        List of all analyses with metadata
    """
    client = _get_chroma_client()

    try:
        collection = client.get_collection("company_analyses")
    except Exception:
        return []

    # Get all items
    results = collection.get()

    formatted_results = []
    if results and results["ids"]:
        for i, doc_id in enumerate(results["ids"]):
            formatted_results.append({
                "id": doc_id,
                "document": results["documents"][i] if results["documents"] else "",
                "metadata": results["metadatas"][i] if results["metadatas"] else {},
            })

    return formatted_results


def clear_collection(collection_name: str = "company_analyses") -> bool:
    """Clear all data from a collection.

    Args:
        collection_name: Name of collection to clear

    Returns:
        True if successful
    """
    client = _get_chroma_client()

    try:
        client.delete_collection(name=collection_name)
        return True
    except Exception:
        return False


def search_by_company(company_name: str, role: str | None = None) -> list[dict[str, Any]]:
    """Search for analyses of a specific company.

    Args:
        company_name: Company name to search for
        role: Optional role filter

    Returns:
        List of matching analyses
    """
    results = retrieve_similar_analyses(company_name, role, n_results=5)
    return results


def get_analysis_context(
    companies: list[str],
    role: str | None = None,
) -> str:
    """Get context from previous analyses to inform current search.

    Args:
        companies: List of companies to get context for
        role: Target role

    Returns:
        Formatted context string for LLM
    """
    all_context = []

    for company in companies:
        analyses = search_by_company(company, role)
        if analyses:
            # Use most relevant analysis
            analysis = analyses[0]
            metadata = analysis.get("metadata", {})
            all_context.append(f"Previous analysis of {company}: Score {metadata.get('score', 'N/A')}")

    return "\n".join(all_context) if all_context else ""
