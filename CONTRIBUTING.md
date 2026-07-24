# Contributing

Thanks for looking! This is an educational demo, but issues and PRs are welcome — **the most useful
contribution is more eval cases**, because that's what makes the chart's grounding + verdict logic
trustworthy.

## Run it locally

```bash
pip install -e .
pip install pytest
pytest -q                 # offline (fake client) — no API key needed
```

CI runs `pytest -q` on every push; keep it green. The full eval (`python evals/run_evals.py`) calls
the model, so it needs an `ANTHROPIC_API_KEY`.

## Add an eval case (most valuable)

Add one JSON object to `evals/dataset/cases.json`:

```json
{ "name": "my-case",
  "claim": "A device comprising A, B and C.",
  "reference": "...prior-art text...",
  "planted_disclosed": [1, 2],
  "expected_verdict": "novel over the reference" }
```

`planted_disclosed` lists which limitations the reference actually discloses (by index — mirror an
existing case); `expected_verdict` is `"anticipated"` or `"novel over the reference"`. Especially
welcome: **harder claim types** — means-plus-function, Markush groups, preamble-heavy claims.

## Guidelines

- Use **synthetic or public** patent text only — never confidential drafts.
- Keep the framing: single-reference anticipation illustration, **not legal advice**.
- Keep PRs small and focused; `pytest -q` must stay green.
