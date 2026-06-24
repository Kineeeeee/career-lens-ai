"""Career Lens AI - Streamlit Web Interface with RAG Support.

This is the main UI for Career Lens AI using Streamlit.
Features:
- Interactive company comparison
- Real-time analysis with RAG retrieval
- Chat history and follow-up questions
- Visualization of scores and rankings
- Export results
"""

import json
import os
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# Import our services
from services.analyze import analyze_company
from services.rag import (
    get_all_analyses,
    get_analysis_context,
    retrieve_similar_analyses,
    store_company_analysis,
)
from services.scoring import rank_companies
from services.search import build_context, search_company

# Load environment variables
load_dotenv()

# Configure Streamlit page
st.set_page_config(
    page_title="Career Lens AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
    <style>
    .score-good { color: #00AA00; font-weight: bold; }
    .score-medium { color: #FF8800; font-weight: bold; }
    .score-low { color: #FF0000; font-weight: bold; }
    .company-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        background: linear-gradient(135deg, #f5f5f5 0%, #ffffff 100%);
    }
    .section-header {
        font-size: 24px;
        font-weight: bold;
        margin-top: 20px;
        margin-bottom: 10px;
        border-bottom: 3px solid #0066cc;
        padding-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)


def score_color_class(score: float) -> str:
    """Determine CSS class based on score."""
    if score >= 75:
        return "score-good"
    elif score >= 50:
        return "score-medium"
    else:
        return "score-low"


def display_company_card(company_data: dict, show_evidence: bool = True):
    """Display a formatted company analysis card."""
    st.markdown("<div class='company-card'>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.markdown(f"### {company_data['company']}")
        analysis = company_data.get("analysis", {})
        st.markdown(f"**Role:** {company_data['role']}")

    with col2:
        score = company_data.get("score", 0)
        confidence = analysis.get("confidence", 0)
        color_class = score_color_class(score)
        st.markdown(
            f"<div class='{color_class}'>Score: {score:.1f}/100</div>",
            unsafe_allow_html=True,
        )
        st.markdown(f"Confidence: {confidence}%")

    with col3:
        if score >= 75:
            st.markdown("✅ **RECOMMENDED**")
        elif score >= 50:
            st.markdown("⚠️ **CONSIDER**")
        else:
            st.markdown("❌ **RISKY**")

    st.divider()

    # Summary
    if summary := analysis.get("summary"):
        st.markdown(f"**Summary:** {summary}")

    if role_fit := analysis.get("role_fit_summary"):
        st.markdown(f"**Role Fit:** {role_fit}")

    # Scores breakdown
    scores = analysis.get("scores", {})
    if scores:
        st.markdown("**Dimension Scores:**")
        score_cols = st.columns(4)
        score_items = list(scores.items())
        for idx, (dimension, score) in enumerate(score_items):
            with score_cols[idx % 4]:
                st.metric(
                    label=dimension.replace("_", " ").title(),
                    value=f"{score}/10",
                    delta=None,
                )

    # Pros and Cons
    col1, col2 = st.columns(2)

    with col1:
        if pros := analysis.get("pros"):
            st.markdown("**✅ Pros:**")
            for pro in pros:
                st.markdown(f"• {pro}")

    with col2:
        if cons := analysis.get("cons"):
            st.markdown("**⚠️ Cons:**")
            for con in cons:
                st.markdown(f"• {con}")

    # Evidence
    if show_evidence:
        if evidence := analysis.get("evidence"):
            st.markdown("**📚 Evidence & Sources:**")
            for i, ev in enumerate(evidence[:3], 1):
                source_title = ev.get("source_title", "Unknown")
                source_url = ev.get("source_url", "")
                claim = ev.get("claim", "")

                if source_url:
                    st.markdown(
                        f"{i}. [{source_title}]({source_url})\n"
                        f"   *{claim}*"
                    )
                else:
                    st.markdown(f"{i}. {source_title}\n   *{claim}*")

    # Recommendation
    if recommendation := analysis.get("recommendation"):
        st.markdown(f"**💡 Recommendation:** {recommendation}")

    st.markdown("</div>", unsafe_allow_html=True)


def init_session_state():
    """Initialize Streamlit session state."""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "analyses" not in st.session_state:
        st.session_state.analyses = []

    if "current_role" not in st.session_state:
        st.session_state.current_role = ""

    if "current_companies" not in st.session_state:
        st.session_state.current_companies = []


def main():
    """Main Streamlit app."""
    init_session_state()

    # Sidebar
    st.sidebar.markdown("# ⚙️ Career Lens AI Settings")

    st.sidebar.markdown("### Input Parameters")
    companies_input = st.sidebar.text_area(
        "Companies to compare (one per line):",
        value="\n".join(st.session_state.current_companies),
        height=100,
    )

    role = st.sidebar.text_input(
        "Target Role:",
        value=st.session_state.current_role,
        placeholder="e.g., AI Engineer, Product Manager",
    )

    location = st.sidebar.text_input(
        "Location (optional):",
        placeholder="e.g., San Francisco, Remote",
    )

    st.sidebar.markdown("### Analysis Options")
    show_evidence = st.sidebar.checkbox("Show Evidence & Sources", value=True)
    use_rag = st.sidebar.checkbox("Use RAG (retrieve previous analyses)", value=True)

    # Main content
    st.markdown("# 🎯 Career Lens AI")
    st.markdown("*AI-powered assistant for evaluating companies for your target role*")

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Analysis",
        "💬 Chat History",
        "📚 RAG Database",
        "📝 All Analyses",
    ])

    with tab1:
        st.markdown("## Company Analysis & Comparison")

        if st.button("🚀 Analyze Companies", use_container_width=True):
            if not companies_input.strip():
                st.error("❌ Please enter at least one company")
                return

            if not role.strip():
                st.error("❌ Please enter a target role")
                return

            companies = [c.strip() for c in companies_input.split("\n") if c.strip()]

            # Update session state
            st.session_state.current_companies = companies
            st.session_state.current_role = role

            # Show progress
            progress_container = st.container()
            progress_bar = progress_container.progress(0, text="Starting analysis...")

            try:
                analyses = []
                rag_context = ""

                if use_rag:
                    rag_context = get_analysis_context(companies, role)
                    if rag_context:
                        st.info(f"📌 Retrieved previous context from RAG:\n{rag_context}")

                for idx, company in enumerate(companies):
                    progress_pct = (idx + 1) / len(companies)
                    progress_bar.progress(
                        progress_pct,
                        text=f"Analyzing {company}...",
                    )

                    # Search company info
                    search_results = search_company(company, role, location)

                    # Build context from search results
                    context = build_context(search_results)

                    # Analyze with LLM
                    analysis_data = analyze_company(
                        company_name=company,
                        role=role,
                        context=context,
                        location=location,
                    )

                    # Store in RAG
                    if use_rag and analysis_data:
                        store_company_analysis(
                            company,
                            role,
                            analysis_data,
                            analysis_data.get("evidence", []),
                        )

                    # Wrap analysis data with company info
                    analyses.append({
                        "company": company,
                        "role": role,
                        "location": location,
                        "search": search_results,
                        "analysis": analysis_data,
                    })

                progress_bar.empty()

                # Rank companies
                ranked = rank_companies(analyses)

                # Store in session
                st.session_state.analyses = ranked

                # Add to chat history
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": f"Compare {', '.join(companies)} for {role}",
                    "timestamp": datetime.now().isoformat(),
                })

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": f"Analyzed {len(companies)} companies. Top choice: {ranked[0]['company']} ({ranked[0]['score']:.1f}/100)",
                    "timestamp": datetime.now().isoformat(),
                })

                st.success(f"✅ Analysis complete! Found {len(ranked)} companies.")

            except Exception as e:
                progress_bar.empty()
                st.error(f"❌ Error during analysis: {str(e)}")
                return

        # Display results
        if st.session_state.analyses:
            st.markdown(f"## 🏆 Results for: {st.session_state.current_role}")
            st.markdown(f"Comparing: {', '.join(st.session_state.current_companies)}")

            st.divider()

            # Display ranking
            for idx, company_data in enumerate(st.session_state.analyses, 1):
                col1, col2 = st.columns([0.5, 9.5])
                with col1:
                    st.markdown(f"## #{idx}")
                with col2:
                    display_company_card(company_data, show_evidence)

            # Comparison table
            st.markdown("## 📊 Detailed Comparison")

            comparison_data = []
            for company in st.session_state.analyses:
                row = {
                    "Company": company["company"],
                    "Score": f"{company['score']:.1f}",
                    "Confidence": f"{company.get('analysis', {}).get('confidence', 0)}%",
                }
                if scores := company.get("analysis", {}).get("scores"):
                    row.update({k: f"{v}/10" for k, v in scores.items()})
                comparison_data.append(row)

            st.dataframe(comparison_data, use_container_width=True)

            # Export results
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 Download as JSON"):
                    json_str = json.dumps(
                        st.session_state.analyses,
                        indent=2,
                        ensure_ascii=False,
                    )
                    st.download_button(
                        label="Download JSON",
                        data=json_str,
                        file_name=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                    )

            with col2:
                if st.button("📋 Copy Results to Clipboard"):
                    st.success("✅ Results copied! (Open browser console)")

    with tab2:
        st.markdown("## 💬 Chat History")

        if st.session_state.chat_history:
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    st.markdown(f"**🧑 You:** {message['content']}")
                else:
                    st.markdown(f"**🤖 Assistant:** {message['content']}")
                st.markdown(f"*{message['timestamp']}*")
                st.divider()

            if st.button("🗑️ Clear Chat History"):
                st.session_state.chat_history = []
                st.rerun()
        else:
            st.info("No chat history yet. Start by analyzing companies!")

    with tab3:
        st.markdown("## 📚 RAG Database")

        if st.button("🔄 Refresh RAG Database"):
            st.rerun()

        all_analyses = get_all_analyses()

        if all_analyses:
            st.success(f"Found {len(all_analyses)} analyses in database")

            for analysis in all_analyses:
                st.markdown(f"**ID:** `{analysis['id']}`")
                metadata = analysis.get("metadata", {})
                st.markdown(
                    f"Company: {metadata.get('company')} | "
                    f"Role: {metadata.get('role')} | "
                    f"Score: {metadata.get('score')}"
                )
                st.divider()

            if st.button("🗑️ Clear RAG Database"):
                from services.rag import clear_collection
                if clear_collection():
                    st.success("✅ RAG database cleared")
                    st.rerun()
                else:
                    st.error("❌ Failed to clear database")
        else:
            st.info("RAG database is empty. Run some analyses first!")

    with tab4:
        st.markdown("## 📝 All Analyses")

        if st.session_state.analyses:
            for company in st.session_state.analyses:
                display_company_card(company, show_evidence)
        else:
            st.info("No analyses yet. Start by analyzing companies in the Analysis tab!")


if __name__ == "__main__":
    main()
