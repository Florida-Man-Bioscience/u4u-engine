"use client";

interface Props {
  treatmentOn: boolean;
  onChange: (next: boolean) => void;
  peptideName?: string | null;
}

/**
 * Page-level switch: include the peptide effect (θ) in the predictive
 * curve, or show the θ = 0 baseline counterfactual. Observed points
 * stay either way.
 */
export function TreatmentEffectToggle({
  treatmentOn,
  onChange,
  peptideName,
}: Props) {
  const label = peptideName
    ? `${peptideName} effect on prediction`
    : "Treatment effect on prediction";
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white px-4 py-3">
      <div className="min-w-0">
        <p className="text-sm font-medium text-slate-800">{label}</p>
        <p className="text-xs text-slate-600">
          {treatmentOn
            ? "Charts show the model with the peptide on (posterior θ)."
            : "Charts show the no-treatment counterfactual (θ = 0, stays at baseline). Observed points stay."}{" "}
          Model overlay only — not a clinical claim.
        </p>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={treatmentOn}
        aria-label={label}
        onClick={() => onChange(!treatmentOn)}
        className={`relative inline-flex h-7 w-12 shrink-0 items-center rounded-full border transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-700 ${
          treatmentOn
            ? "border-teal-700 bg-teal-700"
            : "border-slate-300 bg-slate-200"
        }`}
      >
        <span
          aria-hidden
          className={`inline-block h-5 w-5 rounded-full bg-white shadow transition-transform ${
            treatmentOn ? "translate-x-6" : "translate-x-1"
          }`}
        />
      </button>
    </div>
  );
}
