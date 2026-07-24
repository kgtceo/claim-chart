"""Run the claim-chart eval suite.

Gates (deterministic, against planted labels of which limitation indices ARE disclosed):
  • RECALL     — of the limitations the reference discloses, a solid share are marked disclosed.
  • PRECISION  — NO limitation that isn't disclosed is marked disclosed (no false disclosure).
  • GROUNDING  — every 'disclosed' mapping's quote is a verbatim substring of the reference.
  • VERDICT    — the produced verdict matches the case's declared `expected_verdict`, and the
                 declared verdict is cross-checked against the planted labels (a mislabelled
                 dataset fails loudly instead of silently passing).
  • JUDGE      — (optional, --judge) opus scores chart faithfulness.

Every run writes a reproducible artifact to evals/results/latest.json (metrics, per-case
outcomes, models used, timestamp) — the numbers quoted in the README come from that file.

    python evals/run_evals.py            # deterministic gates only (no opus)
    python evals/run_evals.py --judge    # also run the opus faithfulness judge
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from anthropic import Anthropic

from claim_chart.chart import ChartBuilder
from claim_chart.client import LLMClient
from claim_chart.config import Settings

from metrics import (  # noqa: E402
    is_grounded,
    no_false_disclosure,
    precision,
    recall,
)

DATASET = Path(__file__).parent / "dataset" / "cases.json"
RESULTS = Path(__file__).parent / "results" / "latest.json"

RECALL_THRESHOLD = 0.6  # must catch a solid share of the truly-disclosed limitations


def verdict_matches(result_verdict: str, expected_verdict: str) -> bool:
    """The tool emits 'anticipated' or 'novel over the reference (…)'; the dataset declares
    'anticipated' or 'novel'."""
    if expected_verdict == "anticipated":
        return result_verdict == "anticipated"
    return result_verdict.startswith("novel over the reference")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", action="store_true", help="Also run the opus faithfulness judge.")
    args = ap.parse_args()

    settings = Settings.from_env()
    anthropic = Anthropic(api_key=settings.anthropic_api_key)
    client = LLMClient(settings, anthropic)
    builder = ChartBuilder(client)
    cases = json.loads(DATASET.read_text())

    failures: list[str] = []
    per_case: list[dict] = []
    grades = []
    recalls: list[float] = []
    precisions: list[float] = []
    verdict_hits = 0

    for case in cases:
        result = builder.chart(case["claim"], case["reference"])
        planted = case["planted_disclosed"]
        expected_verdict = case["expected_verdict"]
        rec = recall(result, planted)
        prec = precision(result, planted)
        grounded = is_grounded(result, case["reference"])
        v_ok = verdict_matches(result.verdict, expected_verdict)
        recalls.append(rec)
        precisions.append(prec)

        # Dataset self-consistency: the declared expected_verdict must agree with the planted
        # labels ('anticipated' iff every segmented limitation is planted disclosed).
        derived = "anticipated" if len(set(planted)) == len(result.limitations) else "novel"
        if derived != expected_verdict:
            failures.append(
                f"{case['name']}: DATASET LABEL MISMATCH — expected_verdict={expected_verdict!r} "
                f"but planted labels imply {derived!r} ({len(set(planted))}/{len(result.limitations)} disclosed)"
            )

        print(f"\n=== {case['name']} ===")
        print(f"  recall={rec:.2f} precision={prec:.2f} grounded={grounded} verdict={result.verdict!r}")

        if not grounded:
            failures.append(f"{case['name']}: a 'disclosed' quote isn't in the reference (grounding)")
        if not no_false_disclosure(result, planted):
            failures.append(f"{case['name']}: marked an undisclosed limitation as disclosed (false disclosure / precision)")
        if rec < RECALL_THRESHOLD:
            failures.append(f"{case['name']}: missed too many truly-disclosed limitations (recall {rec:.2f} < {RECALL_THRESHOLD})")
        if v_ok:
            verdict_hits += 1
        else:
            failures.append(f"{case['name']}: verdict {result.verdict!r} != expected {expected_verdict!r}")

        record: dict = {
            "name": case["name"],
            "source": case.get("source"),
            "recall": round(rec, 3),
            "precision": round(prec, 3),
            "grounded": grounded,
            "verdict": result.verdict,
            "expected_verdict": expected_verdict,
            "verdict_correct": v_ok,
        }

        if args.judge:
            from judge import grade  # noqa: E402

            g = grade(result, case["claim"], case["reference"], settings, client)
            grades.append(g)
            record["judge"] = g.model_dump()
            print(f"  JUDGE: faithfulness={g.faithfulness} completeness={g.completeness} verdict_soundness={g.verdict_soundness} overall={g.overall}")
            if g.faithfulness < 3:
                failures.append(f"{case['name']}: judge flagged poor faithfulness (over-reading the reference)")

        per_case.append(record)

    if grades:
        n = len(grades)
        print(f"\n=== Judge avg === overall={sum(g.overall for g in grades)/n:.2f}")

    artifact = {
        "run": {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "model": settings.model,
            "judge_model": settings.judge_model if args.judge else None,
            "dataset_size": len(cases),
        },
        "metrics": {
            "recall_avg": round(sum(recalls) / len(recalls), 3) if recalls else None,
            "precision_avg": round(sum(precisions) / len(precisions), 3) if precisions else None,
            "verdicts": f"{verdict_hits}/{len(cases)}",
            "judge_overall_avg": round(sum(g.overall for g in grades) / len(grades), 2) if grades else None,
            "all_gates_passed": not failures,
        },
        "failures": failures,
        "per_case": per_case,
    }
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(json.dumps(artifact, indent=2) + "\n")
    print(f"\nWrote {RESULTS.relative_to(Path(__file__).parent.parent)}")

    print("\n" + "=" * 40)
    if failures:
        print(f"FAILED ({len(failures)}):")
        for f in failures:
            print(f"  ✗ {f}")
        return 1
    print("ALL GATES PASSED ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
