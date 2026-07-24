"use client";

import { useEffect, useRef, useState } from "react";
import { chart, getSamples } from "../lib/api";
import type { ChartResult, Sample } from "../lib/types";

function sampleLabel(name: string): string {
  if (name.startsWith("real-patent-us5960411")) return "Amazon 1-Click — US 5,960,411";
  return name.replace(/-/g, " ");
}

export default function Home() {
  const [claim, setClaim] = useState("");
  const [reference, setReference] = useState("");
  const [samples, setSamples] = useState<Sample[]>([]);
  const [result, setResult] = useState<ChartResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getSamples()
      .then(setSamples)
      .catch(() => { /* samples optional */ });
  }, []);

  async function run() {
    if (!claim.trim() || !reference.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await chart(claim, reference));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  function loadSample(s: Sample) {
    setClaim(s.claim);
    setReference(s.reference);
    setResult(null);
  }

  const exampleIdx = useRef(0);

  function loadExample() {
    if (samples.length === 0) return;
    loadSample(samples[exampleIdx.current % samples.length]);
    exampleIdx.current += 1;
  }

  const anticipated = result?.verdict.startsWith("anticipated");

  return (
    <div className="container">
      <header>
        <h1>claim-chart</h1>
        <p>
          Paste an independent patent claim and a piece of prior art. It splits the claim into its
          limitations and, for each one, either finds a verbatim quote in the reference (disclosed)
          or marks it not disclosed — then gives a novelty verdict.
        </p>
      </header>

      <div className="banner">
        ⚠️ Educational tool, <strong>not legal advice</strong>. It illustrates an anticipation
        analysis against a single reference; it doesn&rsquo;t assess obviousness, validity, or
        infringement. Use synthetic or public patent text only.
      </div>

      <label htmlFor="claim">Independent claim</label>
      <textarea
        id="claim"
        value={claim}
        placeholder="A method comprising: …; wherein …; and …"
        onChange={(e) => setClaim(e.target.value)}
      />

      <label htmlFor="ref">Prior-art reference</label>
      <textarea
        id="ref"
        value={reference}
        placeholder="Paste the prior-art disclosure here…"
        onChange={(e) => setReference(e.target.value)}
      />

      <div className="actions">
        <button onClick={run} disabled={loading}>
          {loading ? "Charting…" : "Build claim chart"}
        </button>
        <button className="ghost" onClick={loadExample} disabled={loading || samples.length === 0}>
          Load sample
        </button>
      </div>

      {samples.length > 0 && (
        <div className="examples">
          {samples.map((s) => (
            <span className="chip" key={s.name} onClick={() => loadSample(s)}>
              {sampleLabel(s.name)}
              {s.tag && <span className="tag">{s.tag}</span>}
            </span>
          ))}
        </div>
      )}

      {error && <div className="error">{error}</div>}

      {result && (
        <div className="panel">
          <div>
            <span className={`risk ${anticipated ? "high" : "low"}`}>
              {anticipated ? "ANTICIPATED" : "NOVEL OVER THE REFERENCE"}
            </span>
          </div>
          <p style={{ margin: "10px 0" }}>{result.verdict}</p>

          <table className="chart">
            <thead>
              <tr>
                <th style={{ width: 32 }}>#</th>
                <th>Limitation</th>
                <th style={{ width: 130 }}>Disclosed?</th>
                <th>Quote from reference</th>
              </tr>
            </thead>
            <tbody>
              {result.limitations.map((lim, i) => {
                const m = result.mappings[i];
                return (
                  <tr key={lim.index}>
                    <td className="idx">{lim.index}</td>
                    <td>{lim.text}</td>
                    <td>
                      {m?.disclosed ? (
                        <span className="disc yes">✓ disclosed</span>
                      ) : (
                        <span className="disc no">✗ not disclosed</span>
                      )}
                    </td>
                    <td className="quote">{m?.disclosed && m.quote ? `“${m.quote}”` : "—"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {result.novel_because.length > 0 && (
            <div className="novel">
              <strong>Novel because these limitations are not disclosed:</strong>
              <ul>
                {result.novel_because.map((t, i) => (
                  <li key={i}>{t}</li>
                ))}
              </ul>
            </div>
          )}

          <p className="disc-note">{result.disclaimer}</p>
        </div>
      )}
    </div>
  );
}
