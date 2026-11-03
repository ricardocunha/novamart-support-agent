import numpy as np

from novamart_agent.retrieval import PolicyIndex, chunk_markdown

VOCAB = ["return", "electronics", "gift", "shipping", "loyalty"]


class FakeEmbedder:
    """Keyword-count vectors: deterministic, offline, and obvious to reason about."""

    def __init__(self):
        self.calls = 0

    def __call__(self, texts, kind):
        self.calls += 1
        return np.array([[t.lower().count(w) for w in VOCAB] for t in texts], dtype=float)


def doc(doc_id, sections):
    body = "".join(f"## {h}\n{t}\n\n" for h, t in sections)
    return (
        f"---\ndoc_id: {doc_id}\ntitle: {doc_id} title\nowner: x\n"
        f"last_updated: 2026-01-01\nversion: 1\n---\n\n{body}"
    )


DOCS = {
    "a.md": doc("DOC-A", [("Returns", "return return window"), ("Gift", "gift cards gift")]),
    "b.md": doc("DOC-B", [("Shipping", "shipping shipping times"), ("Electronics", "electronics return")]),
}


def write_docs(tmp_path, docs=DOCS):
    d = tmp_path / "policies"
    d.mkdir(exist_ok=True)
    for name, text in docs.items():
        (d / name).write_text(text)
    return d


def test_search_ranks_most_similar_chunk_first(tmp_path):
    chunks = [c for t in DOCS.values() for c in chunk_markdown(t)]
    index = PolicyIndex.build(chunks, FakeEmbedder())
    hits = index.search("shipping question", k=2)
    assert hits[0]["chunk_id"] == "DOC-B#shipping"
    assert hits[0]["score"] > 0.99


def test_search_drops_hits_below_min_score(tmp_path):
    chunks = [c for t in DOCS.values() for c in chunk_markdown(t)]
    index = PolicyIndex.build(chunks, FakeEmbedder())
    assert index.search("loyalty points", k=3, min_score=0.3) == []


def test_search_respects_k(tmp_path):
    chunks = [c for t in DOCS.values() for c in chunk_markdown(t)]
    index = PolicyIndex.build(chunks, FakeEmbedder())
    assert len(index.search("return electronics gift shipping", k=2, min_score=0.0)) == 2


def test_load_or_build_reuses_cache_when_docs_unchanged(tmp_path):
    policies, cache = write_docs(tmp_path), tmp_path / "index.npz"
    PolicyIndex.load_or_build(policies, cache, FakeEmbedder())
    second = FakeEmbedder()
    index = PolicyIndex.load_or_build(policies, cache, second)
    assert second.calls == 0
    assert index.search("gift", k=1)[0]["chunk_id"] == "DOC-A#gift"


def test_load_or_build_rebuilds_when_a_doc_changes(tmp_path):
    policies, cache = write_docs(tmp_path), tmp_path / "index.npz"
    PolicyIndex.load_or_build(policies, cache, FakeEmbedder())
    (policies / "a.md").write_text(doc("DOC-A", [("Loyalty", "loyalty loyalty")]))
    rebuilt = FakeEmbedder()
    index = PolicyIndex.load_or_build(policies, cache, rebuilt)
    assert rebuilt.calls == 1
    assert index.search("loyalty", k=1)[0]["chunk_id"] == "DOC-A#loyalty"


def test_load_or_build_rebuilds_when_embedder_identity_changes(tmp_path):
    policies, cache = write_docs(tmp_path), tmp_path / "index.npz"
    PolicyIndex.load_or_build(policies, cache, FakeEmbedder(), embedder_id="model-a/768")
    other = FakeEmbedder()
    PolicyIndex.load_or_build(policies, cache, other, embedder_id="model-b/768")
    assert other.calls == 1
