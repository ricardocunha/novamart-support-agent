"""Runtime configuration (env-driven, with defaults that work out of the box)."""

import os
from pathlib import Path

from dotenv import load_dotenv
from google.genai import types

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

AGENT_MODEL = os.getenv("NOVAMART_AGENT_MODEL", "gemini-3.5-flash")
JUDGE_MODEL = os.getenv("NOVAMART_JUDGE_MODEL", "gemini-3.1-pro-preview")
EMBEDDING_MODEL = os.getenv("NOVAMART_EMBEDDING_MODEL", "gemini-embedding-001")

POLICY_DIR = ROOT / "docs" / "policies"
DATA_DIR = Path(os.getenv("NOVAMART_DATA_DIR", ROOT / "data"))
INDEX_PATH = ROOT / "data" / "index.npz"
ORDERS_PATH = ROOT / "data" / "orders.json"

# Cosine similarity floor below which a chunk is treated as "not relevant".
# Recall-oriented floor: covered queries scored 0.65-0.79, uncovered 0.51-0.63 (see README).
# The model makes the final relevance call; this only trims obvious noise.
MIN_RETRIEVAL_SCORE = float(os.getenv("NOVAMART_MIN_SCORE", "0.55"))

# Mock signed-in employees. In production these come from the SSO identity token.
PERSONAS = {
    "associate": {"employee_name": "Jordan", "role": "associate", "store_id": "S-042"},
    "manager": {"employee_name": "Alex", "role": "manager", "store_id": "S-042"},
}
DEFAULT_ROLE = os.getenv("NOVAMART_ROLE", "associate")

# Retry transient Gemini errors (429 quota, 503 overloaded) with exponential backoff.
HTTP_RETRY = types.HttpRetryOptions(
    attempts=6, initial_delay=2.0, max_delay=30.0, http_status_codes=[429, 500, 503]
)
