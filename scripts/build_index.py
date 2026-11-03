"""Rebuild data/index.npz if any policy document changed. Usage: uv run python scripts/build_index.py"""

from novamart_agent.config import INDEX_PATH, POLICY_DIR
from novamart_agent.embeddings import GeminiEmbedder
from novamart_agent.retrieval import PolicyIndex

if __name__ == "__main__":
    index = PolicyIndex.load_or_build(POLICY_DIR, INDEX_PATH, GeminiEmbedder())
    print(f"Index ready at {INDEX_PATH}")
