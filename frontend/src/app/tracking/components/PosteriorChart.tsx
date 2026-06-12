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

  const scatter = measurements
    .map((m) => {
      const w = toWeeks(treatmentStartIso, m.measured_at);
      return w === null ? null : { x: w, observed: m.value };
    })
    .filter((d): d is { x: number; observed: number } => d !== null)
    .sort((a, b) => a.x - b.x);

  const band =
    prediction?.posterior_predictive.points.map((p) => ({
      x: p.weeks_since_start,
      mean: p.mean,
      lo: p.lo_95,
      width: p.hi_95 - p.lo_95,
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

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart margin={{ top: 10, right: 20, bottom: 5, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis
          dataKey="x"
          type="number"
          domain={[0, Math.ceil(xMax)]}
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
        <YAxis stroke="#64748b" fontSize={11} domain={["auto", "auto"]} />
        <Tooltip
          formatter={(value: number, name: string) => [Number(value).toFixed(2), name]}
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

        {/* 95% credible band on the posterior predictive mean.
            Implemented as stacked areas: lo (transparent) + width (translucent). */}
        <Area
          data={band}
          dataKey="lo"
          stroke="transparent"
          fill="transparent"
          stackId="ci"
          isAnimationActive={false}
          legendType="none"
        />
        <Area
          data={band}
          dataKey="width"
          name="posterior 95% CI"
          stroke="transparent"
          fill="#0f766e"
          fillOpacity={0.16}
          stackId="ci"
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
  );
}
