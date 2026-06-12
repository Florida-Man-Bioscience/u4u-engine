"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { BiomarkerCatalogEntry, Measurement } from "../lib/types";

interface Props {
  measurements: Measurement[];
  /** Pass the panel entry to overlay the expected timeframe window. */
  expected?: BiomarkerCatalogEntry | null;
  /** Optional treatment-start anchor so x-axis can be "weeks since start". */
  treatmentStartIso?: string | null;
  height?: number;
}

function toWeeks(start: string, when: string): number | null {
  const a = new Date(start);
  const b = new Date(when);
  if (isNaN(a.getTime()) || isNaN(b.getTime())) return null;
  return (b.getTime() - a.getTime()) / (7 * 86_400_000);
}

export function BiomarkerLineChart({
  measurements,
  expected,
  treatmentStartIso,
  height = 260,
}: Props) {
  const useWeeks = Boolean(treatmentStartIso);
  const dataAll = measurements
    .map((m) => {
      if (useWeeks && treatmentStartIso) {
        const w = toWeeks(treatmentStartIso, m.measured_at);
        return w === null ? null : { x: Number(w.toFixed(2)), value: m.value };
      }
      const t = new Date(m.measured_at).getTime();
      return isNaN(t) ? null : { x: t, value: m.value };
    })
    .filter((d): d is { x: number; value: number } => d !== null)
    .sort((a, b) => a.x - b.x);
  // In weeks mode, drop pre-treatment points (x < 0) from the plot so
  // the X axis can hard-clip at 0. In date mode the raw timestamp is
  // always positive so nothing to filter.
  const data = useWeeks ? dataAll.filter((d) => d.x >= 0) : dataAll;
  const preTreatmentCount =
    useWeeks ? dataAll.length - data.length : 0;

  if (data.length === 0) {
    return (
      <div className="rounded border border-slate-200 bg-slate-50 px-4 py-6 text-sm text-slate-500">
        {preTreatmentCount > 0
          ? `${preTreatmentCount} pre-treatment measurement${preTreatmentCount === 1 ? "" : "s"} only — nothing to plot post-treatment yet.`
          : "No measurements recorded yet."}
      </div>
    );
  }

  const xMin = useWeeks ? 0 : data[0].x;
  const xMax = data[data.length - 1].x;
  const expectedBand =
    useWeeks &&
    expected &&
    (expected.timeframe_weeks_min !== null ||
      expected.timeframe_weeks_max !== null);

  return (
    <div className="space-y-2">
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 10, right: 20, bottom: 5, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis
          dataKey="x"
          type="number"
          domain={[xMin, xMax]}
          allowDataOverflow
          tickFormatter={(v) =>
            useWeeks ? `${v}w` : new Date(v).toLocaleDateString()
          }
          stroke="#64748b"
          fontSize={11}
          label={
            useWeeks
              ? {
                  value: "weeks since treatment start",
                  position: "insideBottom",
                  offset: -2,
                  fontSize: 11,
                  fill: "#64748b",
                }
              : undefined
          }
        />
        <YAxis stroke="#64748b" fontSize={11} domain={["auto", "auto"]} />
        <Tooltip
          labelFormatter={(v) =>
            useWeeks ? `${v} weeks` : new Date(Number(v)).toLocaleString()
          }
          formatter={(value: number) => [value, "value"]}
        />
        {expectedBand && (
          <ReferenceArea
            x1={expected.timeframe_weeks_min ?? xMin}
            x2={expected.timeframe_weeks_max ?? xMax}
            fill={
              expected.direction === "increase"
                ? "#bbf7d0"
                : expected.direction === "decrease"
                ? "#fecaca"
                : "#e0e7ff"
            }
            fillOpacity={0.35}
            stroke="none"
            label={{
              value: `expected: ${expected.direction}`,
              position: "insideTop",
              fill: "#475569",
              fontSize: 11,
            }}
          />
        )}
        <Line
          type="monotone"
          dataKey="value"
          stroke="#0f766e"
          strokeWidth={2}
          dot={{ r: 3 }}
          activeDot={{ r: 5 }}
          isAnimationActive={false}
        />
        <Legend wrapperStyle={{ fontSize: 11 }} />
      </LineChart>
    </ResponsiveContainer>
      {preTreatmentCount > 0 && (
        <p className="px-1 text-xs leading-snug text-slate-500">
          {preTreatmentCount} pre-treatment baseline measurement
          {preTreatmentCount === 1 ? "" : "s"} not shown on the chart.
        </p>
      )}
    </div>
  );
}
