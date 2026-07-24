"""FastAPI wrapper: submit a patent claim + prior-art reference → a grounded claim chart."""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .config import Settings
from .data import SAMPLE_CASES
from .models import ChartResult

app = FastAPI(title="claim-chart", version="1.0.0")

_env_origins = [o.strip() for o in os.getenv("CH_CORS_ORIGINS", "").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_env_origins,
    allow_origin_regex=r"https://claim-chart[a-z0-9-]*\.vercel\.app|http://(localhost|127\.0\.0\.1):\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChartRequest(BaseModel):
    claim: str = Field(..., min_length=20, max_length=20000)
    reference: str = Field(..., min_length=20, max_length=40000)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/samples")
def samples() -> dict:
    return {
        "samples": [
            {"name": c.name, "claim": c.claim, "reference": c.reference, "note": c.note, "tag": c.tag}
            for c in SAMPLE_CASES
        ]
    }


@app.post("/api/chart")
def chart(req: ChartRequest) -> ChartResult:
    try:
        settings = Settings.from_env()
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    from .chart import chart as build_chart
    from .client import LLMClient

    return build_chart(req.claim, req.reference, LLMClient(settings))
