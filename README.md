# Career Lens AI

Career Lens AI evaluates and compares companies for a target role using Tavily search, Groq-based analysis, weighted scoring, retrieval-augmented context, and a Streamlit interface.

## Features

- Multi-company evaluation for a specific job role
- Tavily-backed web research with evidence collection
- Structured Groq analysis and weighted scoring
- RAG storage for reusing prior analyses
- Streamlit UI and CLI entry points
- JSON export and chat-style follow-up support

## Quick Start

```bash
python setup.py
copy .env.example .env
streamlit run app_streamlit.py
```

Set `TAVILY_API_KEY` and `GROQ_API_KEY` in `.env` before running the app.

## CLI Example

```bash
python main.py --companies OpenAI Anthropic --role "AI Engineer"
```

## Project Layout

```text
career-lens-ai/
|-- app_streamlit.py
|-- main.py
|-- config.py
|-- helpers.py
|-- prompts/evaluation.txt
`-- services/
   |-- analyze.py
   |-- chat.py
   |-- rag.py
   |-- scoring.py
   `-- search.py
```

## Notes

- Generated analysis data and local vector storage are intentionally kept out of version control.
- `prompts/evaluation.txt` is required by the analysis pipeline and must remain in the repository.
