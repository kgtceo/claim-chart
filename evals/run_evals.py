"""Run the claim-chart eval suite.

Gates (deterministic, against planted labels of which limitation indices ARE disclosed):
  • RECALL     — of the limitations the reference discloses, a solid share are marked disclosed.
  • PRECISION  — NO limitation that isn't disclosed is marked disclosed (no false disclosure).
  • GROUNDING  — every 'disclosed' mapping's quote is a verbatim substring of the reference.
  • VERDICT    — 'anticipated' iff every limitation is disclosed; else 'novel over the reference'.
  • JUDGE      — (optional, --judge) opus scores chart faithfulness.

    python evals/run_evals.py            # deterministic gates only (no opus)
    python evals/run_evals.py --judge    # also run the opus faithfulness judge
"""

from __future__ import annotations

import argparse
import json
import sys
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
    verdict_correct,
)

DATASET = Path(__file__).parent / "dataset" / "cases.json"

RECALL_THRESHOLD = 0.6  # must catch a solid share of the truly-disclosed limitations


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
    grades = []
    for case in cases:
        result = builder.chart(case["claim"], case["reference"])
        planted = case["planted_disclosed"]
        rec = recall(result, planted)
        prec = precision(result, planted)
        grounded = is_grounded(result, case["reference"])
        v_ok = verdict_correct(result, planted)

        print(f"\n=== {case['name']} ===")
        print(f"  recall={rec:.2f} precision={prec:.2f} grounded={grounded} verdict={result.verdict!r}")

        if not grounded:
            failures.append(f"{case['name']}: a 'disclosed' quote isn't in the reference (grounding)")
        if not no_false_disclosure(result, planted):
            failures.append(f"{case['name']}: marked an undisclosed limitation as disclosed (false disclosure / precision)")
        if rec < RECALL_THRESHOLD:
            failures.append(f"{case['name']}: missed too many truly-disclosed limitations (recall {rec:.2f} < {RECALL_THRESHOLD})")
        if not v_ok:
            failures.append(f"{case['name']}: verdict is wrong given the disclosures")

        if args.judge:
            from judge import grade  # noqa: E402

            g = grade(result, case["claim"], case["reference"], settings, client)
            grades.append(g)
            print(f"  JUDGE: faithfulness={g.faithfulness} completeness={g.completeness} verdict_soundness={g.verdict_soundness} overall={g.overall}")
            if g.faithfulness < 3:
                failures.append(f"{case['name']}: judge flagged poor faithfulness (over-reading the reference)")

    if grades:
        n = len(grades)
        print(f"\n=== Judge avg === overall={sum(g.overall for g in grades)/n:.2f}")

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
