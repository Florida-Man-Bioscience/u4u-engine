"use client";

import Link from "next/link";
import { useState } from "react";

interface FaqItem {
  q: string;
  /** Answer as an array of paragraphs. */
  a: string[];
}

const FAQS: FaqItem[] = [
  {
    q: "What is the difference between a peptide and a hormone?",
    a: [
      "A peptide is a short chain of amino acids — the same building blocks that make up proteins, just far fewer of them (typically 2–50, versus hundreds in a full protein). \"Peptide\" describes a molecule's structure: what it is made of, not what it does.",
      "A hormone is defined by its job, not its structure: it is any signalling molecule that one part of the body releases to change the behaviour of cells elsewhere. Hormones come in several chemical families — some are steroids built from cholesterol (testosterone, cortisol), some are derived from single amino acids (thyroid hormone, adrenaline), and many are themselves peptides.",
      "So the two categories overlap rather than compete. Insulin, growth hormone, glucagon, and GLP-1 are all peptides that are also hormones — peptide hormones. But plenty of peptides are not hormones (for example, a structural collagen fragment or a lab-made research peptide that never circulates as an endogenous signal), and plenty of hormones are not peptides (steroid and amino-acid-derived hormones).",
      "For therapy this distinction matters practically. Because peptides are chains of amino acids, the gut digests them like food, so most peptide drugs are injected rather than swallowed, and they tend to be highly specific to their target receptor. Several peptides in this platform's panel — the GLP-1 receptor agonists (semaglutide, tirzepatide, liraglutide) and the growth-hormone-axis peptides (CJC-1295, tesamorelin) — act precisely because they mimic or modulate the body's own peptide hormones.",
    ],
  },
  {
    q: "What does PeptOdyssey actually analyse?",
    a: [
      "You upload a genome file (a VCF, a 23andMe/AncestryDNA text export, or a CSV of genotypes). The engine validates and parses it, filters to high-quality variants, resolves rsIDs, and annotates each variant against ClinVar, gnomAD, Ensembl VEP, UniProt, PharmGKB, and the GWAS Catalog.",
      "It then maps those variants onto peptide-relevant biology — receptor genetics, pathway involvement, polygenic risk, and pharmacogenomics — and produces a prioritised, per-peptide report describing which therapies align with your genetics and how confident that alignment is.",
    ],
  },
  {
    q: "What do the A–D evidence grades mean?",
    a: [
      "Each peptide-and-biomarker effect is tagged with an evidence grade from A to D that reflects the depth of the underlying human research, not the size of the effect. Grade A means the effect is anchored to strong human randomised-controlled-trial data; grade D means it rests largely on preclinical or mechanistic evidence.",
      "The grade is not cosmetic: it tightens or widens the statistical prior the model starts from. Well-evidenced markers (for example, the GLP-1 class for body weight and HbA1c) get a tighter, more confident prior; weakly evidenced ones get a wider prior that defers more to your own measured data.",
    ],
  },
  {
    q: "How should I read the projections on a patient's page?",
    a: [
      "A projection combines two things: a prior — what your genetics and the published evidence predict before any of your own data is seen — and a likelihood — what your recorded measurements over time actually show. A Bayesian update fuses them into a posterior with a 95% credible interval, drawn as a shaded band around the projected trajectory.",
      "The band is the honest part: a wide band means the model is still uncertain (little data, weak evidence), and a narrow band means the data and prior agree. Everything past your most recent measurement is forward projection at the current dose, not a fitted value.",
    ],
  },
  {
    q: "How do you measure whether the modelling is any good?",
    a: [
      "The Model diagnostics page runs a leave-one-out backtest: it hides each recorded measurement in turn, refits the model on everything else, and scores the prediction for the hidden point against what was really observed.",
      "That yields three honest numbers — average error, error spread, and 95%-band coverage (how often the true value landed inside the model's stated confidence band). Coverage near 95% means the uncertainty bands are trustworthy; well below means the model is over-confident. It is an internal performance monitor, not a clinical validation.",
    ],
  },
  {
    q: "Is this a medical diagnosis or treatment recommendation?",
    a: [
      "No. PeptOdyssey is a research and decision-support tool. Its variant classifications are an evidence-assembly aid, and any ACMG/AMP interpretation requires sign-out by a qualified human. Nothing here prescribes therapy or replaces a licensed clinician. Discuss any peptide therapy with your own healthcare provider.",
    ],
  },
  {
    q: "What happens to my genetic data?",
    a: [
      "Uploaded files are encrypted in transit and at rest and are auto-deleted within 24 hours of the analysis completing. The tracking and diagnostics features operate on de-identified patient records that you create and own.",
    ],
  },
];

function FaqRow({ item, defaultOpen }: { item: FaqItem; defaultOpen: boolean }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="rounded-lg border border-slate-200 bg-white">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left"
      >
        <span className="font-medium text-slate-800">{item.q}</span>
        <span
          className={`shrink-0 text-teal-700 transition-transform ${
            open ? "rotate-45" : ""
          }`}
          aria-hidden
        >
          +
        </span>
      </button>
      {open && (
        <div className="space-y-3 border-t border-slate-100 px-5 py-4 text-sm leading-relaxed text-slate-600">
          {item.a.map((p, i) => (
            <p key={i}>{p}</p>
          ))}
        </div>
      )}
    </div>
  );
}

export default function FaqPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6 p-6">
      <header>
        <h1 className="text-2xl font-semibold text-slate-800">
          Frequently asked questions
        </h1>
        <p className="mt-1 text-sm text-slate-600">
          Peptide genomics, the science behind the projections, and how we hold
          the model accountable. Still stuck? Start with a{" "}
          <Link href="/peptodyssey/analyze" className="text-teal-700 underline">
            new analysis
          </Link>
          .
        </p>
      </header>

      <div className="space-y-3">
        {FAQS.map((item, i) => (
          <FaqRow key={item.q} item={item} defaultOpen={i === 0} />
        ))}
      </div>
    </div>
  );
}
