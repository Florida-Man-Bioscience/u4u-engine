"use client";

import {
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import type { DiagnosticsPoint } from "../lib/types";

interface Props {
  points: DiagnosticsPoint[];
  height?: number;
}

interface PlotPoint {
  observed: number;
  predicted: number;
  covered: boolean;
  label: string;
  peptide: string;
  biomarker: string;
}

/** % change from the fit baseline — scale-free so every biomarker shares one axis. */
function pctChange(value: number, baseline: number): number {
  const denom = Math.abs(baseline) || 1;
  return (100 * (value - baseline)) / denom;
}

/**
 * Predicted vs. observed change from baseline (as % of baseline). A model that
 * predicts perfectly lands every point on the dashed y = x line. Points inside
 * the model's 95% predictive band are teal; misses are amber.
 */
export function DiagnosticsScatter({ points, height = 380 }: Props) {
  if (points.length === 0) {
    return (
      <div className="rounded border border-slate-200 bg-slate-50 px-4 py-6 text-sm text-slate-500">
        No held-out predictions to plot yet.
      </div>
    );
  }

  const plot: PlotPoint[] = points.map((p) => ({
    observed: pctChange(p.observed, p.baseline),
    predicted: pctChange(p.predicted, p.baseline),
    covered: p.covered,
    label: p.patient_label,
    peptide: p.peptide,
    biomarker: p.biomarker,
  }));

  const covered = plot.filter((p) => p.covered);
  const missed = plot.filter((p) => !p.covered);

  const vals = plot.flatMap((p) => [p.observed, p.predicted]);
  const lo = Math.floor(Math.min(...vals, 0) / 10) * 10;
  const hi = Math.ceil(Math.max(...vals, 0) / 10) * 10;
  const domain: [number, number] = [lo, hi];

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis
          type="number"
          dataKey="observed"
          domain={domain}
          stroke="#64748b"
          fontSize={11}
          tickFormatter={(v) => `${v}%`}
          label={{
            value: "observed change from baseline",
            position: "insideBottom",
            offset: -8,
            fontSize: 11,
            fill: "#64748b",
          }}
        />
        <YAxis
          type="number"
          dataKey="predicted"
          domain={domain}
          stroke="#64748b"
          fontSize={11}
          tickFormatter={(v) => `${v}%`}
          label={{
            value: "predicted change",
            angle: -90,
            position: "insideLeft",
            offset: 20,
            fontSize: 11,
            fill: "#64748b",
          }}
        />
        <ZAxis range={[40, 40]} />
        {/* Perfect-prediction diagonal (y = x). */}
        <ReferenceLine
          segment={[
            { x: domain[0], y: domain[0] },
            { x: domain[1], y: domain[1] },
          ]}
          stroke="#94a3b8"
          strokeDasharray="4 4"
        />
        <Tooltip
          cursor={{ strokeDasharray: "3 3" }}
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null;
            const d = payload[0].payload as PlotPoint;
            return (
              <div className="rounded border border-slate-200 bg-white px-3 py-2 text-xs shadow">
                <div className="font-medium text-slate-800">
                  {d.label} · {d.peptide}
                </div>
                <div className="text-slate-500">{d.biomarker}</div>
                <div className="mt-1 font-mono text-slate-700">
                  observed {d.observed.toFixed(1)}% · predicted{" "}
                  {d.predicted.toFixed(1)}%
                </div>
                <div className={d.covered ? "text-teal-700" : "text-amber-600"}>
                  {d.covered ? "inside 95% band" : "outside 95% band"}
                </div>
              </div>
            );
          }}
        />
        <Scatter
          name="inside 95% band"
          data={covered}
          fill="#0d9488"
          fillOpacity={0.65}
        />
        <Scatter
          name="outside 95% band"
          data={missed}
          fill="#d97706"
          fillOpacity={0.7}
        />
      </ScatterChart>
    </ResponsiveContainer>
  );
}
