# claim-chart

### ▶ Live demo: **[claim-chart.kareemghazal.com](https://claim-chart.kareemghazal.com)**

[![CI](https://github.com/kgtceo/claim-chart/actions/workflows/ci.yml/badge.svg)](https://github.com/kgtceo/claim-chart/actions/workflows/ci.yml)

Paste an independent patent **claim** and a piece of **prior art** (or "Load sample") and get a
**claim chart**: each claim limitation mapped to a verbatim quote in the reference (disclosed) or
marked **not disclosed**, plus a novelty verdict. (First run ~10–20s.)

> **Educational tool — not legal advice.** It illustrates an anticipation analysis against a single
> reference; it does not assess obviousness, validity, or infringement, and it is not a substitute
> for a professional prior-art search. Use synthetic or public patent text only. Consult a
> qualified patent attorney for anything that matters.

![claim-chart: a patent claim's limitations mapped to supporting prior-art text — each disclosed with a verbatim quote or marked not disclosed — plus a novelty verdict](docs/images/screenshot.png)

![claim-chart — architecture and eval harness](docs/images/architecture.png)

## What it does

Anticipation (novelty) is strict: a single prior-art reference "anticipates" a claim only if it
discloses **every** limitation of that claim. `claim-chart` automates the bookkeeping:

1. It splits the independent claim into its **limitations** (elements / steps).
2. For each limitation, the model decides whether the reference **discloses** it and, if so, must
   back it with a **verbatim quote** from the reference.
3. A deterministic **grounding pass** drops any "disclosed" mapping whose quote isn't actually a
   substring of the reference (whitespace-normalised, case-insensitive) — so it **can't invent a
   disclosure**. This is the killer safety feature: the model never gets to hallucinate the fact.
4. Verdict: **anticipated** if every limitation is disclosed, else **novel over the reference**
   (with the specific limitations that aren't disclosed).

Built around one idea — *measure, don't vibe*: it's gated by a **planted-case eval set** where each
reference discloses a known subset of limitations, so recall, precision (no false disclosure) and
grounding are all measured, not asserted.

## Quickstart

**Requirements:** Python ≥3.10 (backend) · Node ≥18 (the `web/` UI). The offline tests need no API key.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env   # add ANTHROPIC_API_KEY

claim-chart demo                          # a baked-in synthetic claim + reference pair
claim-chart demo --case novel-drone-charging
claim-chart chart --claim "A method comprising: A; and B." --reference "The prior art teaches A."
claim-chart chart --claim-file claim.txt --reference-file ref.txt
```

Sample output (`claim-chart demo`) — each limitation mapped to a verbatim quote, then a verdict:

```
╭─────────────────── Claim chart ───────────────────╮
│ ANTICIPATED — 3/3 limitations disclosed            │
╰────────────────────────────────────────────────────╯
 #  Limitation                      Disclosed    Quote from reference
 1  measuring an ambient            ✓ disclosed  "uses a thermistor to measure
    temperature with a sensor                     ambient temperature with a sensor"
 2  a target temperature received   ✓ disclosed  "target temperature ... received from
    from a mobile device                          a mobile device over a wireless link"
 3  activating a heating element    ✓ disclosed  "when the measured temperature falls
    when temp falls below target                  below the target ... activating a
                                                  heating element"
```

A *novel* case shows the un-disclosed limitations and a "novel over the reference" verdict instead.

## Evals

```bash
python evals/run_evals.py             # deterministic gates: recall / precision / grounding / verdict
python evals/run_evals.py --judge     # also run the opus faithfulness judge
```

- **Recall** — of the limitations the reference truly discloses, a solid share are marked disclosed.
- **Precision** — no limitation that *isn't* disclosed is marked disclosed (**no false disclosure**).
- **Grounding** — every "disclosed" quote appears verbatim in the reference.
- **Verdict** — the produced verdict must match the case's declared `expected_verdict`, and that
  declaration is itself cross-checked against the planted labels — a mislabelled dataset fails
  loudly instead of silently passing.
- **Judge** — opus scores chart faithfulness (over-reading), completeness, and verdict soundness.

Every run writes a **reproducible artifact** to [`evals/results/latest.json`](evals/results/latest.json)
— per-case outcomes, metrics, the models used, and a timestamp. The numbers below come from that file.

**Latest run (claude-sonnet-4-6, opus judge):** all gates pass on the **5 labelled claim + prior-art
cases** — disclosure recall **1.00** and precision **1.00** (no false disclosure), every "disclosed"
quote verbatim-grounded, all **5/5** verdicts correct, and the opus judge scores **5.0/5** overall.

Two of the five cases are built to break lazy charting:

- **A real granted claim** — claim 1 of **US 5,960,411 (Amazon "1-Click", 1999, expired)** charted
  against a synthetic conventional shopping-cart system. Three traps, one per single-action
  qualifier: the reference verbatim-contains "sending a request … to a server system" — but *not*
  "in response to **only a single action**"; its server receives requests — but has no
  "**single-action ordering component**"; it fulfils orders — but **with** a cart. The chart must
  resist all three tempting quotes and call the claim novel (which is roughly why the patent was
  granted).
- **A paraphrased anticipation** — every limitation disclosed, but in different words (sprockets =
  "toothed wheels", derailleur = "chain-shifting mechanism"). The opposite failure mode: disclosure
  judged on substance, while the quote must still be verbatim from the reference.

It's a small, hand-labelled set — enough to gate the grounding + verdict logic, not a benchmark;
add your own — each case is one JSON object in `evals/dataset/cases.json`:

```json
{ "name": "my-case",
  "claim": "A device comprising A, B and C.",
  "reference": "...prior-art text...",
  "planted_disclosed": [1, 2],
  "expected_verdict": "novel" }
```

`planted_disclosed` lists which limitations the reference actually discloses (by index — mirror an
existing case); `expected_verdict` is `"anticipated"` or `"novel"`.

## Limitations (what it does NOT do)

- **Single-reference anticipation only** — it charts a claim against *one* reference (a §102-style
  anticipation view). It does **not** assess obviousness (§103) over a combination of references,
  enablement, or overall patentability.
- **Segmentation is deterministic** (semicolons / newlines / "wherein" / ", and" — deliberately
  *not* bare "and", which appears inside single limitations constantly: "a processor and a
  memory"); the LLM only does the disclosed/quote mapping, and the deterministic grounding filter
  + verdict own the outcome. Unusual claim phrasing can still segment imperfectly — treat the
  chart as a **first-pass draft for a human to confirm**.
- Best on **synthetic or public** patent text; it is not a substitute for a professional prior-art
  search or an attorney's invalidity/FTO analysis.

## Tests

```bash
pytest -q   # offline: segmentation, the grounding pass drops fabricated quotes, verdict logic
            # (fake client, no API key, no network)
```

## Web

`web/` — a Next.js UI: two textareas (claim + reference), a limitation-by-limitation chart table
(disclosed / not disclosed + the grounded quote), the novelty verdict, and the not-legal-advice
banner throughout.

Run it locally in two terminals:

```bash
# terminal 1 — the API
pip install -e .
cp .env.example .env                  # add ANTHROPIC_API_KEY
python -m uvicorn claim_chart.api:app --port 8000

# terminal 2 — the UI
cd web
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev                           # open http://localhost:3000
```

See [DEPLOY.md](./DEPLOY.md) — the FastAPI backend on Railway (via the `Dockerfile`; needs
`ANTHROPIC_API_KEY`) + the Next.js `web/` UI on Vercel, ~5 minutes.

## License

MIT — see [LICENSE](./LICENSE).
