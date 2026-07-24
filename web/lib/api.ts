import { FALLBACK_SAMPLES } from "./samples";
import type { ChartResult, Sample } from "./types";

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/+$/, "");

// Never rejects: falls back to the baked-in samples when the API is cold or the
// response isn't the expected shape, so "Load sample" always works.
export async function getSamples(): Promise<Sample[]> {
  try {
    const res = await fetch(`${API_URL}/api/samples`);
    if (!res.ok) throw new Error(`status ${res.status}`);
    const body = await res.json();
    const ok =
      Array.isArray(body?.samples) &&
      body.samples.length > 0 &&
      body.samples.every((s: Sample) => typeof s?.claim === "string" && typeof s?.reference === "string");
    if (!ok) throw new Error("unexpected samples shape");
    return body.samples as Sample[];
  } catch {
    return FALLBACK_SAMPLES;
  }
}

export async function chart(claim: string, reference: string): Promise<ChartResult> {
  const res = await fetch(`${API_URL}/api/chart`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ claim, reference }),
  });
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      /* non-JSON */
    }
    throw new Error(detail);
  }
  return res.json();
}
