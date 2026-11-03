from novamart_agent.retrieval import chunk_markdown

DOC = """---
doc_id: POL-TST-001
title: Test Policy
owner: Ops
last_updated: 2026-01-01
version: 1.0
---

# Test Policy

## Return window
Items can be returned within 30 days.

## Gift cards & vouchers
Gift cards are never refundable.
More text here.
"""


def test_one_chunk_per_h2_section():
    chunks = chunk_markdown(DOC)
    assert [c.section for c in chunks] == ["Return window", "Gift cards & vouchers"]


def test_chunk_id_is_doc_id_plus_slugged_section():
    chunks = chunk_markdown(DOC)
    assert [c.chunk_id for c in chunks] == ["POL-TST-001#return-window", "POL-TST-001#gift-cards-vouchers"]


def test_chunk_carries_front_matter_metadata():
    c = chunk_markdown(DOC)[0]
    assert c.doc_id == "POL-TST-001"
    assert c.title == "Test Policy"
    assert c.last_updated == "2026-01-01"


def test_chunk_text_contains_section_body_only():
    second = chunk_markdown(DOC)[1]
    assert second.text == "Gift cards are never refundable.\nMore text here."
    assert "30 days" not in second.text


def test_embedding_text_includes_title_and_section_for_context():
    c = chunk_markdown(DOC)[0]
    assert c.embedding_text() == "Test Policy — Return window\nItems can be returned within 30 days."
