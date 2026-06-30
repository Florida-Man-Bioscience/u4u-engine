"use client";

import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ReferenceArea,
  ResponsiveContainer,
  Scatter,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { CohortResult } from "../lib/types";

interface Props {
  result: CohortResult;
  height?: number;
}

export function CohortTrajectoryChart({ result, height = 320 }: Props) {
  // Build a unified dataset:
  //  - scatter points: every patient trajectory (weeks vs value)
  //  - per-bin median line + IQR band
  const scatter = result.trajectories.map((t) => ({
    x: t.weeks_since_start,
    value: t.value,
  }));
  // IQR band as an explicit [q1, q3] range tuple. NOT a stacked-area trick:
  // <ComposedChart> here has no chart-level `data` (each series carries its
  // own), and recharts computes stack offsets from chart-level data — so a
  // stacked q1-baseline + iqr area never lifts off the axis and the band
  // collapses to 0..(q3-q1) near the x-axis. A range Area renders q1..q3
  // directly, independent of stacking.
  const band = result.time_bins.map((b) => ({
    x: b.weeks_label,
    median: b.median,
    range: [b.q1, b.q3] as [number, number],
  }));

  const xMax = Math.max(
    ...scatter.map((p) => p.x),
    ...band.map((b) => b.x),
    1
  );
  const exp = result.expected;
  const expectedBand =
    exp && (exp.timeframe_weeks_min !== null || exp.timeframe_weeks_max !== null);

  if (result.n_measurements === 0) {
    return (
      <div className="rounded border border-slate-200 bg-slate-50 px-4 py-6 text-sm text-slate-500">
        No measurements yet for {result.peptide} → {result.biomarker_name}.
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
          formatter={(value: number, name: string) => [value, name]}
          labelFormatter={(v) => `${v} weeks`}
        />
        {expectedBand && (
          <ReferenceArea
            x1={exp.timeframe_weeks_min ?? 0}
            x2={exp.timeframe_weeks_max ?? xMax}
            fill={
              exp.direction === "increase"
                ? "#bbf7d0"
                : exp.direction === "decrease"
                ? "#fecaca"
                : "#e0e7ff"
            }
            fillOpacity={0.3}
            stroke="none"
            label={{
              value: `expected: ${exp.direction}`,
              position: "insideTopLeft",
              fill: "#475569",
              fontSize: 11,
            }}
          />
        )}
        {/* IQR band drawn as a q1..q3 range area (see `band` above). */}
        <Area
          data={band}
          dataKey="range"
          name="IQR (q1–q3)"
          stroke="transparent"
          fill="#0f766e"
          fillOpacity={0.18}
          isAnimationActive={false}
        />
        <Line
          data={band}
          dataKey="median"
          name="cohort median"
          stroke="#0f766e"
          strokeWidth={2}
          dot={{ r: 3 }}
          isAnimationActive={false}
        />
        <Scatter
          data={scatter}
          dataKey="value"
          name="patient measurements"
          fill="#94a3b8"
          isAnimationActive={false}
        />
        <Legend wrapperStyle={{ fontSize: 11 }} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

interface DoseProps {
  result: CohortResult;
  height?: number;
}

export function DoseResponseChart({ result, height = 260 }: DoseProps) {
  const data = result.dose_response.map((d) => ({
    dose: d.dose,
    median: d.median_value,
    n_patients: d.n_patients,
    pct: d.pct_change_from_baseline,
    label: `${d.dose} ${d.dose_unit}`,
  }));
  if (data.length === 0) {
    return (
      <div className="rounded border border-slate-200 bg-slate-50 px-4 py-6 text-sm text-slate-500">
        No dose data — treatments need a numeric dose to appear here.
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart
        data={data}
        margin={{ top: 10, right: 20, bottom: 5, left: 0 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis
          dataKey="dose"
          type="number"
          stroke="#64748b"
          fontSize={11}
          label={{
            value: `dose (${data[0]?.label.split(" ").slice(1).join(" ") || ""})`,
            position: "insideBottom",
            offset: -2,
            fontSize: 11,
            fill: "#64748b",
          }}
        />
        <YAxis stroke="#64748b" fontSize={11} />
        <Tooltip
          formatter={(value: number, name: string) => {
            if (name === "median") return [value, "median value"];
            if (name === "pct") return [value === null ? "—" : `${value}%`, "Δ vs baseline"];
            return [value, name];
          }}
          labelFormatter={(v) => `dose: ${v}`}
        />
        <Scatter
          dataKey="median"
          fill="#0f766e"
          isAnimationActive={false}
          name="median"
        />
        <Legend wrapperStyle={{ fontSize: 11 }} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
