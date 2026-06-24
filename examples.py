#!/usr/bin/env python
"""Example usage of Career Lens AI with RAG support.

This script demonstrates how to use the Career Lens AI API programmatically.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from services.search import search_company
from services.analyze import analyze_company
from services.scoring import rank_companies
from services.rag import store_company_analysis, retrieve_similar_analyses, get_all_analyses
from helpers import format_analysis_for_display, create_comparison_table


def example_1_basic_analysis():
    """Example 1: Basic company analysis."""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Basic Company Analysis")
    print("=" * 70)

    companies = ["Google", "Meta"]
    role = "Backend Engineer"
    location = "San Francisco"

    print(f"\nAnalyzing: {', '.join(companies)}")
    print(f"Role: {role}")
    print(f"Location: {location}")

    analyses = []

    for company in companies:
        print(f"\n🔍 Searching for {company}...")
        search_results = search_company(company, role, location)
        print(f"   Found {len(search_results.get('results', []))} web results")

        print(f"   Analyzing with AI...")
        analysis = analyze_company(company, role, location, search_results)
        analyses.append(analysis)

    # Rank
    print(f"\n📊 Ranking companies...")
    ranked = rank_companies(analyses)

    # Display
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    for idx, company in enumerate(ranked, 1):
        print(f"\n#{idx}. {company['company']} - Score: {company['score']:.1f}/100")
        print(format_analysis_for_display(company))


def example_2_rag_retrieval():
    """Example 2: Using RAG to retrieve previous analyses."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: RAG Retrieval")
    print("=" * 70)

    # Retrieve all stored analyses
    print("\n📚 All stored analyses in RAG database:")
    all_analyses = get_all_analyses()

    if not all_analyses:
        print("   No analyses stored yet.")
        print("   Run analysis through web UI first to populate RAG database!")
    else:
        for idx, analysis in enumerate(all_analyses, 1):
            metadata = analysis.get("metadata", {})
            print(f"\n   #{idx}. {metadata.get('company', 'Unknown')}")
            print(f"       Role: {metadata.get('role', 'N/A')}")
            print(f"       Score: {metadata.get('score', 'N/A')}/100")
            print(f"       Sources: {metadata.get('sources', 'N/A')}")

    # Try to retrieve similar
    if all_analyses:
        print("\n🔎 Retrieving similar to Google + Backend Engineer:")
        similar = retrieve_similar_analyses("Google Backend Engineer", n_results=2)
        if similar:
            print(f"   Found {len(similar)} similar analyses")
            for s in similar:
                print(f"   - {s['metadata'].get('company', 'Unknown')} (similarity: {1 - s['distance']:.2%})")
        else:
            print("   No similar analyses found")


def example_3_comparison_table():
    """Example 3: Creating comparison table."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Comparison Table")
    print("=" * 70)

    # Sample data (in real usage, these would come from analysis)
    sample_analyses = [
        {
            "company": "Google",
            "score": 78.5,
            "analysis": {
                "scores": {
                    "learning": 8,
                    "growth": 7,
                    "compensation": 8,
                    "stability": 9,
                    "work_life_balance": 6,
                    "brand": 9,
                    "role_fit": 8,
                    "risk": 2,
                }
            }
        },
        {
            "company": "Meta",
            "score": 75.2,
            "analysis": {
                "scores": {
                    "learning": 9,
                    "growth": 8,
                    "compensation": 8,
                    "stability": 7,
                    "work_life_balance": 5,
                    "brand": 8,
                    "role_fit": 7,
                    "risk": 4,
                }
            }
        },
    ]

    print("\nComparison Table:")
    print(create_comparison_table(sample_analyses))


def example_4_chat_with_context():
    """Example 4: Using chat with RAG context."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Chat with RAG Context")
    print("=" * 70)

    print("\nNote: Requires API calls. Showing structure only.")
    print("\nHow to use:")
    print("  from services.chat import chat_with_context")
    print("  from services.rag import get_analysis_context")
    print("")
    print("  # Get context from RAG")
    print("  context = get_analysis_context(['Google', 'Meta'], 'Backend Engineer')")
    print("")
    print("  # Ask a question with context")
    print("  response = chat_with_context(")
    print("      'Which company is better for work-life balance?',")
    print("      rag_context=context")
    print("  )")
    print("  print(response)")


def example_5_custom_analysis():
    """Example 5: Running custom analysis with preferences."""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Custom Analysis with Preferences")
    print("=" * 70)

    print("\nYou can customize scoring weights for your priorities:")
    print("\n# Edit config.py")
    print("SCORING_WEIGHTS = {")
    print('    "learning": 0.25,  # Increase learning importance')
    print('    "growth": 0.25,')
    print('    "role_fit": 0.15,  # Decrease role_fit')
    print('    "compensation": 0.10,  # Lower importance')
    print('    "stability": 0.10,')
    print('    "work_life_balance": 0.05,  # Lower importance')
    print('    "brand": 0.05,')
    print('    "risk": 0.05,')
    print("}")
    print("\n# Then run analysis normally - it will use new weights")


def main():
    """Run examples."""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    # Check API keys
    if not os.getenv("TAVILY_API_KEY"):
        print("❌ TAVILY_API_KEY not set in .env")
        print("Please set up your API keys first!")
        return

    if not os.getenv("GROQ_API_KEY"):
        print("❌ GROQ_API_KEY not set in .env")
        print("Please set up your API keys first!")
        return

    print("\n🎯 Career Lens AI - Usage Examples")
    print("=" * 70)

    # Choose example
    print("\nAvailable examples:")
    print("  1. Basic company analysis (requires API calls)")
    print("  2. RAG retrieval (check stored analyses)")
    print("  3. Comparison table (sample data)")
    print("  4. Chat with context (show structure)")
    print("  5. Custom analysis with preferences")
    print("  0. Run all examples")

    try:
        choice = input("\nSelect example (0-5): ").strip()
    except EOFError:
        # Batch mode - run example 2 (no API calls)
        example_2_rag_retrieval()
        example_3_comparison_table()
        example_4_chat_with_context()
        example_5_custom_analysis()
        return

    if choice == "1":
        example_1_basic_analysis()
    elif choice == "2":
        example_2_rag_retrieval()
    elif choice == "3":
        example_3_comparison_table()
    elif choice == "4":
        example_4_chat_with_context()
    elif choice == "5":
        example_5_custom_analysis()
    elif choice == "0":
        print("\nRunning all examples...")
        example_2_rag_retrieval()
        example_3_comparison_table()
        example_4_chat_with_context()
        example_5_custom_analysis()
        print("\n⚠️  Example 1 requires API calls and user input.")
        print("Run 'python examples.py' and select '1' to try it!")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
