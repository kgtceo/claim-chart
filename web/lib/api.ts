import type { ChartResult, Sample } from "./types";

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/+$/, "");

export async function getSamples(): Promise<Sample[]> {
  const res = await fetch(`${API_URL}/api/samples`);
  if (!res.ok) throw new Error(`Could not load samples (${res.status})`);
  const body = await res.json();
  return body.samples as Sample[];
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
