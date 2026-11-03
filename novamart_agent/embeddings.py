"""Gemini embedding adapter matching the retrieval `Embedder` protocol."""

from typing import Literal

import numpy as np
from google import genai
from google.genai import types

from novamart_agent.config import EMBEDDING_MODEL

_TASK = {"document": "RETRIEVAL_DOCUMENT", "query": "RETRIEVAL_QUERY"}


class GeminiEmbedder:
    def __init__(self, model: str = EMBEDDING_MODEL, dimensions: int = 768):
        self._client = genai.Client()  # Gemini API key or Vertex AI, from env
        self._model = model
        self._dims = dimensions

    def __call__(self, texts: list[str], kind: Literal["document", "query"]) -> np.ndarray:
        result = self._client.models.embed_content(
            model=self._model,
            contents=texts,
            config=types.EmbedContentConfig(task_type=_TASK[kind], output_dimensionality=self._dims),
        )
        return np.array([e.values for e in result.embeddings], dtype=float)
