/**
 * Explanatory callout + visual key for the per-biomarker posterior charts.
 *
 * Rendered once above the chart list (not per-chart) so it's not noisy.
 * Collapsible — open by default, but the user can collapse it once they
 * know how to read the charts.
 *
 * Swatch colours mirror the constants in PosteriorChart.tsx exactly:
 *   - expected window:     #bbf7d0 / #fecaca / #e0e7ff (with 0.25 opacity)
 *   - 95% CI band:         #0f766e (teal-700) at 0.16 opacity
 *   - posterior mean line: #0f766e
 *   - prior dashed line:   #64748b (slate-500), dasharray "4 3"
 *   - observed scatter:    #0f172a (slate-900)
 *   - prior-window edges:  #94a3b8 (slate-400), dasharray "3 3"
 *
 * If you change colours in the chart, mirror them here so the key
 * keeps telling the truth.
 */
export function BayesianChartGuide() {
  return (
    <details
      open
      className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm"
    >
      <summary className="cursor-pointer select-none font-medium text-slate-800">
        How to read these charts
      </summary>

      <div className="mt-3 space-y-2 text-xs leading-relaxed text-slate-600">
        <p>
          Each chart combines what the patient&apos;s <strong>genetics</strong>{" "}
          predict for this biomarker (the <em>prior</em>) with what their{" "}
          <strong>measurements</strong> show so far (the <em>likelihood</em>) to
          produce a posterior estimate of the asymptotic change from baseline —
          i.e. how much the marker will move once the peptide&apos;s effect
          plateaus.
        </p>
        <p>
          Before measurements arrive, the prediction sits on the genetic prior.
          As measurements come in, the posterior shifts toward what the
          trajectory actually shows; the gap between the dashed prior line and
          the solid posterior line is the update.
        </p>
      </div>

      <div className="mt-4 grid gap-x-6 gap-y-2 sm:grid-cols-2">
        <KeyItem
          swatch={
            <span
              className="block h-3 w-6 rounded-sm"
              style={{ backgroundColor: "#bbf7d0", opacity: 0.7 }}
              aria-hidden
            />
          }
        >
          <strong>Expected window</strong> — when the biomarker is predicted to
          start changing (left edge) and to plateau (right edge), given the
          posterior. Mint = increase, light red = decrease. Drawn at lower
          opacity when the posterior&apos;s 95% CI doesn&apos;t exclude zero
          (label reads &ldquo;uncertain&rdquo;).
        </KeyItem>

        <KeyItem
          swatch={
            <span
              className="block h-3 w-6 rounded-sm"
              style={{ backgroundColor: "#0f766e", opacity: 0.22 }}
              aria-hidden
            />
          }
        >
          <strong>95% credible interval</strong> — uncertainty around the
          predicted value at each week. Includes both θ uncertainty and (when
          baseline was inferred from the data rather than observed pre-treatment)
          baseline uncertainty.
        </KeyItem>

        <KeyItem
          swatch={
            <span
              className="block h-[2px] w-6"
              style={{ backgroundColor: "#0f766e" }}
              aria-hidden
            />
          }
        >
          <strong>Posterior mean</strong> — predicted trajectory after combining
          the genetic prior with the patient&apos;s measurements.
        </KeyItem>

        <KeyItem
          swatch={
            <span
              className="block h-0 w-6 border-t-2 border-dashed"
              style={{ borderColor: "#64748b" }}
              aria-hidden
            />
          }
        >
          <strong>Prior (genetics only)</strong> — what we predicted before any
          measurements. The gap between this and the posterior shows what the
          data taught us.
        </KeyItem>

        <KeyItem
          swatch={
            <span
              className="block h-2 w-2 rounded-full"
              style={{ backgroundColor: "#0f172a" }}
              aria-hidden
            />
          }
        >
          <strong>Observed measurement</strong> — the patient&apos;s actual lab
          values, time-aligned to treatment start.
        </KeyItem>

        <KeyItem
          swatch={
            <span className="flex h-3 w-6 items-center justify-between">
              <span
                className="block h-3 w-0 border-l border-dashed"
                style={{ borderColor: "#94a3b8" }}
                aria-hidden
              />
              <span
                className="block h-3 w-0 border-l border-dashed"
                style={{ borderColor: "#94a3b8" }}
                aria-hidden
              />
            </span>
          }
        >
          <strong>Prior window edges</strong> — where the expected window sat
          before measurements. Comparing them to the solid posterior window
          shows how the data shifted the timing.
        </KeyItem>
      </div>
    </details>
  );
}

function KeyItem({
  swatch,
  children,
}: {
  swatch: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-start gap-2.5">
      <span className="mt-1 flex h-3 w-6 shrink-0 items-center justify-center">
        {swatch}
      </span>
      <p className="text-xs leading-snug text-slate-600">{children}</p>
    </div>
  );
}
