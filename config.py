# config.py - Configuration file for Career Lens AI

# Model settings
MODEL = "llama-3.3-70b-versatile"
TEMPERATURE = 0.2  # Lower = more deterministic

# Search settings
MAX_SEARCH_RESULTS = 4  # Results per query
CONTEXT_LIMIT = 8  # Max results to include in prompt

# Scoring weights
# Must sum to 1.0
SCORING_WEIGHTS = {
    "learning": 0.18,
    "growth": 0.18,
    "compensation": 0.14,
    "stability": 0.12,
    "work_life_balance": 0.12,
    "brand": 0.08,
    "role_fit": 0.18,
    "risk": 0.10,
}

# Output settings
DATA_DIR = "data/analyses"
SAVE_INDIVIDUAL_ANALYSES = True
SAVE_COMPARISON_REPORT = True

# Display settings
SHOW_EVIDENCE = True
MIN_CONFIDENCE_WARNING = 50  # Warn if confidence below this

# API Retry settings
MAX_RETRIES = 2
RETRY_DELAY = 2  # seconds

# Scoring ranges (for reference)
SCORE_SCALE = {
    "min": 0,
    "max": 100,
    "dimension_min": 0,
    "dimension_max": 10,
}

# RAG Settings
RAG_ENABLED = True  # Enable vector storage for analyses
RAG_DB_PATH = "data/chroma_db"
RAG_SIMILARITY_THRESHOLD = 0.5  # Min similarity score
RAG_MAX_RESULTS = 3  # Max results per query

# Chat settings
CHAT_HISTORY_LIMIT = 20  # Max messages to keep in memory
CHAT_TEMPERATURE = 0.7  # Higher = more creative
FOLLOW_UP_QUESTIONS_COUNT = 3

# Streamlit UI settings
STREAMLIT_THEME = "light"  # light or dark
STREAMLIT_LAYOUT = "wide"  # wide or centered
MAX_COMPANIES_TO_ANALYZE = 10
DEFAULT_RESULTS_PER_PAGE = 5