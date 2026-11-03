"""Policy retrieval: section-level chunking + embedding search.

Deliberately small. In production this is replaced by a Vertex AI Search / Gemini Enterprise
datastore; the `search_policies` tool contract (chunks with citable ids) stays the same.
"""

import hashlib
import json
import re
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import yaml

# (texts, kind) -> (n, dim) array. kind lets real embedders use asymmetric task types.
Embedder = Callable[[list[str], Literal["document", "query"]], np.ndarray]

_FRONT_MATTER = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


@dataclass(frozen=True)
class Chunk:
    doc_id: str
    title: str
    section: str
    text: str
    last_updated: str
    version: str

    @property
    def chunk_id(self) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", self.section.lower()).strip("-")
        return f"{self.doc_id}#{slug}"

    def embedding_text(self) -> str:
        return f"{self.title} — {self.section}\n{self.text}"

    def to_dict(self) -> dict:
        return {"chunk_id": self.chunk_id, **asdict(self)}


def chunk_markdown(markdown: str) -> list[Chunk]:
    match = _FRONT_MATTER.match(markdown)
    if not match:
        raise ValueError("policy document is missing YAML front-matter")
    meta = yaml.safe_load(match.group(1))
    body = markdown[match.end() :]

    chunks = []
    for part in re.split(r"^## ", body, flags=re.MULTILINE)[1:]:
        heading, _, text = part.partition("\n")
        chunks.append(
            Chunk(
                doc_id=str(meta["doc_id"]),
                title=str(meta["title"]),
                section=heading.strip(),
                text=text.strip(),
                last_updated=str(meta["last_updated"]),
                version=str(meta["version"]),
            )
        )
    return chunks


def _normalise(m: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(m, axis=1, keepdims=True)
    return m / np.where(norms == 0, 1, norms)


def _fingerprint(policy_dir: Path, embedder_id: str) -> str:
    """Changes when any doc changes or the embedding model/dimensions change."""
    h = hashlib.sha256(embedder_id.encode())
    for path in sorted(policy_dir.glob("*.md")):
        h.update(path.name.encode())
        h.update(path.read_bytes())
    return h.hexdigest()


class PolicyIndex:
    def __init__(self, chunks: list[Chunk], vectors: np.ndarray, embedder: Embedder):
        self._chunks = chunks
        self._vectors = _normalise(vectors)
        self._embed = embedder

    @classmethod
    def build(cls, chunks: list[Chunk], embedder: Embedder) -> PolicyIndex:
        vectors = embedder([c.embedding_text() for c in chunks], "document")
        return cls(chunks, np.asarray(vectors, dtype=float), embedder)

    @classmethod
    def load_or_build(
        cls, policy_dir: str | Path, cache_path: str | Path, embedder: Embedder, embedder_id: str = ""
    ) -> PolicyIndex:
        policy_dir, cache_path = Path(policy_dir), Path(cache_path)
        fingerprint = _fingerprint(policy_dir, embedder_id)
        if cache_path.exists():
            cached = np.load(cache_path, allow_pickle=False)
            if str(cached["fingerprint"]) == fingerprint:
                chunks = [Chunk(**c) for c in json.loads(str(cached["chunks"]))]
                return cls(chunks, cached["vectors"], embedder)

        chunks = [c for p in sorted(policy_dir.glob("*.md")) for c in chunk_markdown(p.read_text())]
        index = cls.build(chunks, embedder)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez(
            cache_path,
            vectors=index._vectors,
            chunks=json.dumps([asdict(c) for c in chunks]),
            fingerprint=fingerprint,
        )
        return index

    def search(self, query: str, k: int = 4, min_score: float = 0.0) -> list[dict]:
        q = _normalise(np.asarray(self._embed([query], "query"), dtype=float))[0]
        scores = self._vectors @ q
        hits = []
        for i in np.argsort(-scores)[:k]:
            if scores[i] < min_score:
                break
            hits.append({**self._chunks[i].to_dict(), "score": round(float(scores[i]), 4)})
        return hits
