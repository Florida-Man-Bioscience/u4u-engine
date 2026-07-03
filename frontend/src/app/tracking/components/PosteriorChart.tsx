"use client";

import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ReferenceArea,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { BiomarkerCatalogEntry, Measurement, PredictionResult } from "../lib/types";

interface Props {
  measurements: Measurement[];
  treatmentStartIso: string | null;
  expected: BiomarkerCatalogEntry | null;
  prediction: PredictionResult | null;
  height?: number;
}

function toWeeks(start: string, when: string): number | null {
  const a = new Date(start);
  const b = new Date(when);
  if (isNaN(a.getTime()) || isNaN(b.getTime())) return null;
  return (b.getTime() - a.getTime()) / (7 * 86_400_000);
}

export function PosteriorChart({
  measurements,
  treatmentStartIso,
  expected,
  prediction,
  height = 320,
}: Props) {
  if (!treatmentStartIso) {
    return (
      <div className="rounded border border-slate-200 bg-slate-50 px-4 py-6 text-sm text-slate-500">
        Select an active treatment to overlay the Bayesian prediction.
      </div>
    );
  }

  const scatterAll = measurements
    .map((m) => {
      const w = toWeeks(treatmentStartIso, m.measured_at);
      return w === null ? null : { x: w, observed: m.value };
    })
    .filter((d): d is { x: number; observed: number } => d !== null)
    .sort((a, b) => a.x - b.x);
  // X axis is "weeks since treatment start" — negative values would be
  // pre-treatment baseline measurements. They still feed the Bayesian
  // fit upstream of this chart, but plotting them would force Recharts
  // to extend the visible axis below 0 (allowDataOverflow defaults to
  // false), producing meaningless "-2w / -1w" ticks. Drop them from the
  // plot and surface the count in the caption instead.
  const preTreatmentCount = scatterAll.filter((p) => p.x < 0).length;
  const scatter = scatterAll.filter((p) => p.x >= 0);

  const band =
    prediction?.posterior_predictive.points.map((p) => ({
      x: p.weeks_since_start,
      mean: p.mean,
      range: [p.lo_95, p.hi_95] as [number, number],
    })) ?? [];

  const priorBand =
    prediction?.prior_predictive.points.map((p) => ({
      x: p.weeks_since_start,
      prior_mean: p.mean,
    })) ?? [];

  const xMax = Math.max(
    ...scatter.map((p) => p.x),
    ...band.map((p) => p.x),
    1,
  );

  if (scatter.length === 0 && band.length === 0) {
    return (
      <div className="rounded border border-slate-200 bg-slate-50 px-4 py-6 text-sm text-slate-500">
        No measurements or predictions to show.
      </div>
    );
  }

  // ── Y-axis units & domain ─────────────────────────────────────────────
  // Bare numeric ticks confuse the reader — "what does -0.15 mean?" — so
  // we pull the biomarker unit off the catalog entry and attach it to
  // every tick (short units like "%") AND to the axis title (long units
  // like "mg/dL"), choosing whichever reads better. Concentration-like
  // biomarkers can't physically be negative; if every observed and
  // predicted value is ≥ 0 we clamp the lower bound so Recharts doesn't
  // auto-fit a domain that drifts below zero and renders meaningless
  // negative ticks under a wide credible interval.
  const rawUnit = expected?.unit ?? null;
  const SHORT_UNIT_RE = /^[%‰°]$/u;
  const unitSuffix = rawUnit && SHORT_UNIT_RE.test(rawUnit) ? rawUnit : "";
  const unitLabel = rawUnit && !unitSuffix ? rawUnit : "";
  const formatTick = (v: number) => {
    if (Math.abs(v) >= 100) return v.toFixed(0);
    if (Math.abs(v) >= 10) return v.toFixed(1);
    return v.toFixed(2);
  };
  // If the catalog says this marker has a directional response
  // (concentration-style: increase or decrease) AND every observed
  // measurement is ≥ 0, clamp the floor to 0 so a wide credible band
  // can't drag the axis into negatives the biomarker never actually
  // takes.
  const observedFloor =
    scatter.length > 0 ? Math.min(...scatter.map((p) => p.observed)) : Infinity;
  const directional =
    expected?.direction === "increase" || expected?.direction === "decrease";
  const clampToZero = directional && observedFloor >= 0;
  const yDomain: [number | string, number | string] = clampToZero
    ? [0, "auto"]
    : ["auto", "auto"];

  // Plain-English caption for the shaded "expected window" so users
  // don't have to flip back to the legend to know what the colour means
  // on THIS chart (the meaning depends on direction — increase / decrease
  // / variable — and shading colour swaps accordingly).
  const shadingMeta = (() => {
    const w = prediction?.expected_window;
    const direction = w?.direction ?? expected?.direction ?? null;
    if (!direction) return null;
    const credible = w?.credible ?? true;
    const asymptotePct = w
      ? `${w.asymptote_pct_change >= 0 ? "+" : ""}${(w.asymptote_pct_change * 100).toFixed(0)}%`
      : null;
    if (direction === "increase") {
      return {
        swatch: "#bbf7d0",
        text: asymptotePct
          ? `Green shading: weeks during which the marker is expected to rise toward its predicted plateau (${asymptotePct}).`
          : "Green shading: weeks during which the marker is expected to rise toward its predicted plateau.",
        credible,
      };
    }
    if (direction === "decrease") {
      return {
        swatch: "#fecaca",
        text: asymptotePct
          ? `Red shading: weeks during which the marker is expected to drop toward its predicted plateau (${asymptotePct}).`
          : "Red shading: weeks during which the marker is expected to drop toward its predicted plateau.",
        credible,
      };
    }
    return {
      swatch: "#e0e7ff",
      text: "Indigo shading: weeks during which the marker is expected to change toward its predicted plateau.",
      credible,
    };
  })();

  return (
    <div className="space-y-2">
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart margin={{ top: 10, right: 20, bottom: 5, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis
          dataKey="x"
          type="number"
          domain={[0, Math.ceil(xMax)]}
          allowDataOverflow
          tickFormatter={(v) => `${v}w`}
          stroke="#64748b"
          fontSize={11}
          label={{
            value: "weeks since treatment start",
            position: "insideBottom",
            offset: -2,
            fontSize: 11,
            fill: "#64748b",
          }}
        />
        <YAxis
          stroke="#64748b"
          fontSize={11}
          domain={yDomain}
          width={56}
          tickFormatter={(v) =>
            unitSuffix ? `${formatTick(v)}${unitSuffix}` : formatTick(v)
          }
          label={
            unitLabel
              ? {
                  value: unitLabel,
                  angle: -90,
                  position: "insideLeft",
                  offset: 6,
                  fontSize: 11,
                  fill: "#64748b",
                  style: { textAnchor: "middle" },
                }
              : undefined
          }
        />
        <Tooltip
          formatter={(value: number, name: string) => [
            unitSuffix
              ? `${Number(value).toFixed(2)}${unitSuffix}`
              : Number(value).toFixed(2),
            name,
          ]}
          labelFormatter={(v) => `${v} weeks`}
        />
        {(() => {
          // Projection region — weeks past the last observed measurement.
          // Rendered first so it sits behind everything; a light grey
          // wash and a dashed vertical boundary mark "forward projection"
          // so the user can distinguish it from the fitted region.
          const lastObserved = prediction?.last_observed_week ?? null;
          if (
            lastObserved === null ||
            lastObserved === undefined ||
            lastObserved >= xMax
          ) {
            return null;
          }
          return (
            <>
              <ReferenceArea
                x1={lastObserved}
                x2={xMax}
                fill="#0f172a"
                fillOpacity={0.04}
                stroke="none"
                label={{
                  value: "projection →",
                  position: "insideTopRight",
                  fill: "#64748b",
                  fontSize: 10,
                }}
              />
              <ReferenceLine
                x={lastObserved}
                stroke="#64748b"
                strokeDasharray="2 4"
                strokeWidth={1}
                label={{
                  value: "last measurement",
                  position: "insideTop",
                  fill: "#64748b",
                  fontSize: 10,
                  offset: 10,
                }}
              />
            </>
          );
        })()}
        {(() => {
          // Bayes-informed window from the posterior, with a dashed
          // outline of the prior-only window so the user can see how the
          // measurements shifted the expected timeframe. Falls back to
          // the static panel range when no prediction is available.
          const w = prediction?.expected_window;
          const priorW = prediction?.prior_expected_window;
          const x1 = w ? w.weeks_min : (expected?.timeframe_weeks_min ?? null);
          const x2 = w ? w.weeks_max : (expected?.timeframe_weeks_max ?? null);
          if (x1 === null && x2 === null) return null;
          const direction = w?.direction ?? expected?.direction ?? "variable";
          const credible = w?.credible ?? true;
          const fill =
            direction === "increase"
              ? "#bbf7d0"
              : direction === "decrease"
                ? "#fecaca"
                : "#e0e7ff";
          const label = w
            ? `posterior: ${direction}${credible ? "" : " (uncertain)"} · asymptote ${(w.asymptote_pct_change * 100).toFixed(0)}%`
            : `expected: ${direction}`;
          return (
            <>
              <ReferenceArea
                x1={x1 ?? 0}
                x2={x2 ?? xMax}
                fill={fill}
                fillOpacity={credible ? 0.25 : 0.12}
                stroke="none"
                label={{
                  value: label,
                  position: "insideTopLeft",
                  fill: "#475569",
                  fontSize: 11,
                }}
              />
              {priorW && (
                <>
                  <ReferenceLine
                    x={priorW.weeks_min}
                    stroke="#94a3b8"
                    strokeDasharray="3 3"
                    label={{
                      value: "prior window",
                      position: "top",
                      fill: "#94a3b8",
                      fontSize: 10,
                    }}
                  />
                  <ReferenceLine
                    x={priorW.weeks_max}
                    stroke="#94a3b8"
                    strokeDasharray="3 3"
                  />
                </>
              )}
            </>
          );
        })()}

        {/* 95% credible band on the posterior predictive mean, drawn as an
            explicit [lo_95, hi_95] range Area. NOT a stacked-area trick: each
            <Area> carries its own `data` (no chart-level data), so recharts
            can't compute stack offsets and a stacked lo-baseline + width
            collapses to 0..width pinned at the x-axis. A range Area positions
            lo..hi directly. (Same fix as CohortChart's IQR band.) */}
        <Area
          data={band}
          dataKey="range"
          name="posterior 95% CI"
          stroke="transparent"
          fill="#0f766e"
          fillOpacity={0.16}
          isAnimationActive={false}
        />
        {/* Prior-only mean curve as a dashed line for comparison. */}
        <Line
          data={priorBand}
          dataKey="prior_mean"
          name="prior (genetics only)"
          stroke="#64748b"
          strokeWidth={1.5}
          strokeDasharray="4 3"
          dot={false}
          isAnimationActive={false}
        />
        <Line
          data={band}
          dataKey="mean"
          name="posterior mean"
          stroke="#0f766e"
          strokeWidth={2}
          dot={false}
          isAnimationActive={false}
        />
        <Scatter
          data={scatter}
          dataKey="observed"
          name="observed"
          fill="#0f172a"
          isAnimationActive={false}
        />
        <Legend wrapperStyle={{ fontSize: 11 }} />
      </ComposedChart>
    </ResponsiveContainer>
      <div className="space-y-1 px-1 text-xs leading-snug text-slate-600">
        {preTreatmentCount > 0 && (
          <p className="text-slate-500">
            {preTreatmentCount} pre-treatment baseline measurement
            {preTreatmentCount === 1 ? "" : "s"} not shown on the chart
            (still applied to the Bayesian fit).
          </p>
        )}
        {band.length > 0 && (
          <p className="flex items-start gap-2">
            <span
              className="mt-[3px] inline-block h-3 w-4 shrink-0 rounded-sm"
              style={{ backgroundColor: "#0f766e", opacity: 0.22 }}
              aria-hidden
            />
            <span>
              <strong>Teal band</strong> wrapping the posterior mean line:
              the 95% credible interval — where the model thinks the next
              measurement is likely to land at each week. When the band
              hugs the bottom of the chart, the model is predicting little
              to no change.
            </span>
          </p>
        )}
        {shadingMeta && (
          <p className="flex items-start gap-2">
            <span
              className="mt-[3px] inline-block h-3 w-4 shrink-0 rounded-sm"
              style={{
                backgroundColor: shadingMeta.swatch,
                opacity: shadingMeta.credible ? 0.7 : 0.4,
              }}
              aria-hidden
            />
            <span>
              {shadingMeta.text}
              {!shadingMeta.credible && (
                <span className="text-slate-500">
                  {" "}
                  (lighter shade — the 95% credible interval still includes
                  zero, so the direction itself is uncertain).
                </span>
              )}
            </span>
          </p>
        )}
      </div>
    </div>
  );
}
