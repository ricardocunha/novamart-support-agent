from evals.scoring import Transcript, score_case


def transcript(answer, calls=(), retrieved=()):
    return Transcript(
        answer=answer, tool_calls=[{"name": n, "args": {}} for n in calls], retrieved_ids=set(retrieved)
    )


ANSWER = "No — electronics have a 15-day window [POL-RET-001#category-exceptions]."


def test_all_expectations_met_passes():
    result = score_case(
        {
            "tools_called": ["search_policies", "get_order_status"],
            "cites": ["POL-RET-001"],
            "must_include": [r"15[- ]day"],
        },
        transcript(ANSWER, ["get_order_status", "search_policies"], ["POL-RET-001#category-exceptions"]),
    )
    assert result["passed"] is True
    assert all(result["checks"].values())


def test_missing_tool_call_fails_that_check():
    result = score_case({"tools_called": ["get_order_status"]}, transcript(ANSWER, ["search_policies"]))
    assert result["checks"]["tools_called"] is False
    assert result["passed"] is False


def test_forbidden_tool_call_fails():
    result = score_case({"tools_not_called": ["log_knowledge_gap"]}, transcript("Hi", ["log_knowledge_gap"]))
    assert result["checks"]["tools_not_called"] is False


def test_missing_required_citation_fails():
    result = score_case(
        {"cites": ["POL-SHP-006"]}, transcript(ANSWER, retrieved=["POL-RET-001#category-exceptions"])
    )
    assert result["checks"]["cites"] is False


def test_citation_not_retrieved_this_run_is_flagged_as_fabricated():
    result = score_case({}, transcript(ANSWER, retrieved=[]))
    assert result["checks"]["citations_grounded"] is False


def test_must_include_is_case_insensitive_regex_and_must_not_include_blocks():
    result = score_case(
        {"must_include": ["ELECTRONICS"], "must_not_include": [r"30[- ]day"]},
        transcript(ANSWER, retrieved=["POL-RET-001#category-exceptions"]),
    )
    assert result["checks"]["must_include"] is True
    assert result["checks"]["must_not_include"] is True


def test_must_not_include_hit_fails():
    result = score_case(
        {"must_not_include": ["15-day"]}, transcript(ANSWER, retrieved=["POL-RET-001#category-exceptions"])
    )
    assert result["checks"]["must_not_include"] is False
