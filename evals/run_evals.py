"""Run the eval set against the live agent and write evals/report.md.

Usage: uv run python -m evals.run_evals [--no-judge] [--only ID ...] [--concurrency 3]
"""

import argparse
import asyncio
import os
import tempfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import yaml

# Reproducible clock, and keep eval tickets/gaps out of the demo data dir. Must precede agent import.
os.environ.setdefault("NOVAMART_TODAY", "2026-11-03")
os.environ["NOVAMART_DATA_DIR"] = tempfile.mkdtemp(prefix="novamart-eval-")

from evals.scoring import Transcript, score_case  # noqa: E402
from novamart_agent.config import AGENT_MODEL, JUDGE_MODEL  # noqa: E402
from novamart_agent.session import AgentSession  # noqa: E402

HERE = Path(__file__).parent


async def run_case(case: dict, judge, sem: asyncio.Semaphore) -> dict:
    async with sem:
        session = AgentSession(role=case.get("role", "associate"))
        turns = case.get("turns") or [case["question"]]
        calls, results, answer = [], [], ""
        for text in turns:
            turn = await session.ask(text)
            calls += turn.tool_calls
            results += turn.tool_results
            answer = turn.answer  # score the final answer; tool usage across all turns

        retrieved = {
            r["chunk_id"]
            for res in results
            if res["name"] == "search_policies"
            for r in (res["response"] or {}).get("results", [])
        }
        t = Transcript(answer=answer, tool_calls=calls, retrieved_ids=retrieved)
        det = score_case(case.get("expect", {}), t)
        verdict = await judge.grade("\n".join(turns), answer, results, case["reference"]) if judge else None
        passed = det["passed"] and (verdict is None or verdict["passed"])
        mark = "PASS" if passed else "FAIL"
        print(f"[{mark}] {case['id']}")
        return {
            "case": case,
            "answer": answer,
            "tools": [c["name"] for c in calls],
            **det,
            "judge": verdict,
            "passed": passed,
        }


def write_report(rows: list[dict], judged: bool) -> Path:
    total = len(rows)
    ok = sum(r["passed"] for r in rows)
    by_cat = defaultdict(lambda: [0, 0])
    for r in rows:
        by_cat[r["case"]["category"]][0] += r["passed"]
        by_cat[r["case"]["category"]][1] += 1

    lines = [
        "# Eval report",
        "",
        f"Run {datetime.now():%Y-%m-%d %H:%M} · agent `{AGENT_MODEL}` · "
        f"judge `{JUDGE_MODEL if judged else 'disabled'}` · clock {os.environ['NOVAMART_TODAY']}",
        "",
        f"**{ok}/{total} passed ({ok / total:.0%})**",
        "",
        "| Category | Passed |",
        "|---|---|",
        *[f"| {c} | {p}/{n} |" for c, (p, n) in sorted(by_cat.items())],
    ]
    if judged:
        js = [r["judge"] for r in rows if r["judge"]]
        if js:
            lines += [
                "",
                f"Mean judge scores over {len(js)} graded cases: "
                f"faithfulness **{sum(j['faithfulness'] for j in js) / len(js):.2f}**, "
                f"correctness **{sum(j['correctness'] for j in js) / len(js):.2f}** (1–5)",
            ]
    lines += ["", "## Cases", "", "| | Case | Tools | Failed checks | Judge (F/C) |", "|---|---|---|---|---|"]
    for r in rows:
        failed = ", ".join(k for k, v in r["checks"].items() if not v) or "—"
        j = f"{r['judge']['faithfulness']}/{r['judge']['correctness']}" if r["judge"] else "—"
        lines.append(
            f"| {'✅' if r['passed'] else '❌'} | `{r['case']['id']}` | {', '.join(r['tools']) or '—'} "
            f"| {failed} | {j} |"
        )
    failures = [r for r in rows if not r["passed"]]
    if failures:
        lines += ["", "## Failures", ""]
        for r in failures:
            lines += [
                f"### `{r['case']['id']}`",
                "",
                f"**Expected:** {r['case']['reference']}",
                "",
                "**Answer:**",
                "",
                "> " + r["answer"].replace("\n", "\n> "),
                "",
            ]
            if r["judge"]:
                lines += [f"**Judge:** {r['judge']['rationale']}", ""]
    out = HERE / "report.md"
    out.write_text("\n".join(lines) + "\n")
    return out


async def _safe(coro, case: dict) -> dict:
    """An API failure (quota, outage) marks one case as errored instead of aborting the run."""
    try:
        return await coro
    except Exception as e:  # noqa: BLE001
        print(f"[ERROR] {case['id']}: {type(e).__name__}")
        return {
            "case": case,
            "answer": f"ERROR: {str(e)[:300]}",
            "tools": [],
            "checks": {"ran": False},
            "judge": None,
            "passed": False,
        }


async def main(args) -> int:
    cases = yaml.safe_load((HERE / "cases.yaml").read_text())
    if args.only:
        cases = [c for c in cases if c["id"] in args.only]
    judge = None
    if not args.no_judge:
        from evals.judge import Judge

        judge = Judge()
    sem = asyncio.Semaphore(args.concurrency)
    rows = await asyncio.gather(*(_safe(run_case(c, judge, sem), c) for c in cases))
    out = write_report(list(rows), judged=judge is not None)
    ok = sum(r["passed"] for r in rows)
    print(f"\n{ok}/{len(rows)} passed — report: {out}")
    return 0 if ok == len(rows) else 1


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--no-judge", action="store_true")
    p.add_argument("--only", nargs="*")
    p.add_argument("--concurrency", type=int, default=3)
    raise SystemExit(asyncio.run(main(p.parse_args())))
