"use client";

import { useCallback, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { analyzeFile } from "./lib/api";
import versionData from "../../version.json";

const ACCEPTED = ".vcf,.txt,.csv";
const MAX_SIZE_MB = 100;

const PIPELINE_STEPS = [
  {
    icon: "01",
    title: "Upload",
    desc: "Drop your genome file — VCF, 23andMe, or CSV format.",
  },
  {
    icon: "02",
    title: "Annotate",
    desc: "Cross-referenced against ClinVar, gnomAD, VEP, UniProt, PharmGKB, and GWAS Catalog.",
  },
  {
    icon: "03",
    title: "Predict",
    desc: "Peptide therapy response prediction based on pathway and receptor genetics.",
  },
  {
    icon: "04",
    title: "Report",
    desc: "Clinically prioritized variant report with per-peptide gene variant mapping.",
  },
];

const PEPTIDE_HIGHLIGHTS = [
  { name: "BPC-157", category: "Multi-Pathway Regenerative", genes: 27 },
  { name: "Thymosin Alpha-1", category: "Immune Modulation", genes: 3 },
  { name: "CJC-1295 + Ipamorelin", category: "Growth Hormone", genes: 1 },
  { name: "Epithalon", category: "Longevity / Telomere", genes: 1 },
  { name: "AOD-9604", category: "Weight Management", genes: 1 },
  { name: "MOTS-c", category: "Metabolic", genes: 1 },
];

export default function LandingPage() {
  const router = useRouter();

  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [medications, setMedications] = useState("");
  const [uploadLoaded, setUploadLoaded] = useState(0);
  const [uploadTotal, setUploadTotal] = useState(0);
  const [uploadFraction, setUploadFraction] = useState<number | null>(null);
  const [uploadDone, setUploadDone] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function validateFile(f: File): string | null {
    const ext = f.name.split(".").pop()?.toLowerCase() ?? "";
    if (!["vcf", "txt", "csv"].includes(ext))
      return "Only .vcf, .txt, and .csv files are accepted.";
    if (f.size > MAX_SIZE_MB * 1024 * 1024)
      return `File must be ≤ ${MAX_SIZE_MB} MB.`;
    return null;
  }

  function handleFileChange(f: File) {
    const err = validateFile(f);
    if (err) {
      setError(err);
      setFile(null);
    } else {
      setError(null);
      setFile(f);
    }
  }

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) handleFileChange(f);
  };

  const onDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFileChange(f);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setError(null);
    setSubmitting(true);
    setUploadLoaded(0);
    setUploadTotal(file.size);
    setUploadFraction(0);
    setUploadDone(false);
    try {
      const meds = medications
        .split(",")
        .map((m) => m.trim())
        .filter(Boolean);
      const { job_id } = await analyzeFile(file, {
        currentMedications: meds.length ? meds : undefined,
        onProgress: (p) => {
          setUploadLoaded(p.loaded);
          setUploadTotal(p.total || file.size);
          setUploadFraction(p.fraction);
          setUploadDone(p.done);
        },
      });
      router.push(`/jobs/${job_id}`);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "An unexpected error occurred."
      );
      setSubmitting(false);
      setUploadFraction(null);
      setUploadDone(false);
    }
  }

  function formatBytes(n: number): string {
    if (n < 1024) return `${n} B`;
    if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
    return `${(n / (1024 * 1024)).toFixed(2)} MB`;
  }

  return (
    <div className="space-y-0">
      {/* ── Hero ────────────────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden bg-[#0d1117] -mx-4 -mt-8 px-4 pt-20 pb-24">
        {/* Subtle grid background */}
        <div
          className="absolute inset-0 opacity-[0.04]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.5) 1px, transparent 1px)",
            backgroundSize: "60px 60px",
          }}
        />
        {/* Accent glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-[#1a6b4a]/20 rounded-full blur-[120px]" />

        <div className="relative max-w-3xl mx-auto text-center space-y-6">
          <div className="inline-flex items-center gap-2 rounded-full border border-[#1a6b4a]/40 bg-[#1a6b4a]/10 px-4 py-1.5 text-xs font-medium text-[#2d8f61] tracking-wide uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-[#2d8f61] animate-pulse" />
            Precision Peptide Genomics
          </div>

          <h1
            className="text-5xl sm:text-6xl text-white leading-[1.1] tracking-tight"
            style={{ fontFamily: "'DM Serif Display', serif" }}
          >
            Your Genome.
            <br />
            <span className="text-[#2d8f61]">Your Peptide Map.</span>
          </h1>

          <p className="text-lg text-zinc-400 max-w-xl mx-auto leading-relaxed">
            Upload your genetic data and discover which peptide therapies align
            with your unique biology. Variant-level analysis across 11 candidate
            therapies, powered by 7 annotation engines.
          </p>

          {/* Scroll-to-upload CTA */}
          <a
            href="#upload"
            className="inline-flex items-center gap-2 rounded-lg bg-[#1a6b4a] text-white px-8 py-3.5 text-sm font-semibold hover:bg-[#2d8f61] transition-colors shadow-lg shadow-[#1a6b4a]/25"
          >
            Start Analysis
            <span className="text-lg leading-none">&#x2192;</span>
          </a>
        </div>
      </section>

      {/* ── How it works ────────────────────────────────────────────────────── */}
      <section className="py-16 -mx-4 px-4">
        <div className="max-w-4xl mx-auto">
          <h2
            className="text-2xl text-center text-[#0d1117] mb-10"
            style={{ fontFamily: "'DM Serif Display', serif" }}
          >
            How It Works
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {PIPELINE_STEPS.map((step) => (
              <div
                key={step.icon}
                className="bg-white rounded-xl border border-[#dbd9d3] p-5 space-y-3 hover:shadow-md hover:border-[#1a6b4a]/30 transition-all"
              >
                <span
                  className="text-2xl font-light text-[#1a6b4a]"
                  style={{ fontFamily: "'DM Serif Display', serif" }}
                >
                  {step.icon}
                </span>
                <h3 className="font-semibold text-[#0d1117] text-sm">
                  {step.title}
                </h3>
                <p className="text-xs text-[#6b7280] leading-relaxed">
                  {step.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Peptide Therapy Coverage ────────────────────────────────────────── */}
      <section className="py-16 -mx-4 px-4 bg-white border-y border-[#dbd9d3]">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-10 space-y-2">
            <h2
              className="text-2xl text-[#0d1117]"
              style={{ fontFamily: "'DM Serif Display', serif" }}
            >
              11 Peptide Therapies Evaluated
            </h2>
            <p className="text-sm text-[#6b7280] max-w-lg mx-auto">
              Each therapy is mapped to its target genes. Your variants are
              matched to predict response, efficacy, and safety considerations.
            </p>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {PEPTIDE_HIGHLIGHTS.map((p) => (
              <div
                key={p.name}
                className="rounded-lg border border-[#edecea] bg-[#f5f4f0] p-4 space-y-1"
              >
                <p className="font-semibold text-sm text-[#0d1117]">
                  {p.name}
                </p>
                <p className="text-xs text-[#6b7280]">{p.category}</p>
                <p className="text-xs text-[#1a6b4a] font-medium">
                  {p.genes} target gene{p.genes !== 1 ? "s" : ""}
                </p>
              </div>
            ))}
          </div>
          <p className="text-center text-xs text-[#9ca3af] mt-4">
            Plus Matrixyl, Argireline, SNAP-8, GHK-Cu + BPC-157 + TB-500,
            and BPC-157 + TB-500 combination therapies.
          </p>
        </div>
      </section>

      {/* ── Annotation engines ──────────────────────────────────────────────── */}
      <section className="py-16 -mx-4 px-4">
        <div className="max-w-4xl mx-auto text-center space-y-6">
          <h2
            className="text-2xl text-[#0d1117]"
            style={{ fontFamily: "'DM Serif Display', serif" }}
          >
            7 Annotation Engines
          </h2>
          <div className="flex flex-wrap justify-center gap-3">
            {[
              "Ensembl VEP",
              "NCBI ClinVar",
              "gnomAD",
              "MyVariant.info",
              "UniProt",
              "PharmGKB",
              "GWAS Catalog",
            ].map((engine) => (
              <span
                key={engine}
                className="inline-flex items-center rounded-full border border-[#dbd9d3] bg-white px-4 py-2 text-sm text-[#3a3f4a] font-medium"
              >
                {engine}
              </span>
            ))}
          </div>
          <p className="text-xs text-[#9ca3af] max-w-md mx-auto">
            Results are cached across sessions — repeated variant queries
            resolve instantly from the local database.
          </p>
        </div>
      </section>

      {/* ── Upload form ─────────────────────────────────────────────────────── */}
      <section
        id="upload"
        className="py-16 -mx-4 px-4 bg-[#0d1117] border-t border-[#1a6b4a]/30"
      >
        <div className="max-w-xl mx-auto">
          <div className="text-center mb-8 space-y-2">
            <h2
              className="text-2xl text-white"
              style={{ fontFamily: "'DM Serif Display', serif" }}
            >
              Begin Your Analysis
            </h2>
            <p className="text-sm text-zinc-400">
              Upload a genome file to generate your personalized peptide therapy
              report.
            </p>
          </div>

          <form
            onSubmit={handleSubmit}
            className="bg-[#161b22] rounded-xl border border-[#30363d] p-6 space-y-5"
          >
            {/* Drop zone */}
            <div
              role="button"
              tabIndex={0}
              aria-label="File drop zone"
              className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-10 cursor-pointer transition-colors ${
                dragging
                  ? "border-[#2d8f61] bg-[#1a6b4a]/10"
                  : file
                    ? "border-[#2d8f61] bg-[#1a6b4a]/5"
                    : "border-[#30363d] hover:border-[#2d8f61]/50 hover:bg-[#1a6b4a]/5"
              }`}
              onDragOver={(e) => {
                e.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={onDrop}
              onClick={() => inputRef.current?.click()}
              onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
            >
              <input
                ref={inputRef}
                type="file"
                accept={ACCEPTED}
                className="sr-only"
                onChange={onInputChange}
              />
              {file ? (
                <>
                  <span className="text-[#2d8f61] text-3xl mb-2">&#x2714;</span>
                  <p className="font-medium text-[#2d8f61]">{file.name}</p>
                  <p className="text-xs text-zinc-500 mt-1">
                    {(file.size / 1024 / 1024).toFixed(2)} MB — click to change
                  </p>
                </>
              ) : (
                <>
                  <div className="w-12 h-12 rounded-full bg-[#1a6b4a]/10 flex items-center justify-center mb-3">
                    <span className="text-[#2d8f61] text-xl">&#x2191;</span>
                  </div>
                  <p className="font-medium text-zinc-300">
                    Drag &amp; drop or click to choose
                  </p>
                  <p className="text-xs text-zinc-500 mt-1">
                    .vcf, .txt, .csv — max {MAX_SIZE_MB} MB
                  </p>
                </>
              )}
            </div>

            {/* Current medications (optional) — drives DDGI phenoconversion */}
            <div className="space-y-1.5">
              <label
                htmlFor="medications"
                className="block text-xs font-semibold text-zinc-300 uppercase tracking-wide"
              >
                Current Medications{" "}
                <span className="text-zinc-500 font-normal normal-case tracking-normal">
                  — optional
                </span>
              </label>
              <input
                id="medications"
                type="text"
                value={medications}
                onChange={(e) => setMedications(e.target.value)}
                placeholder="e.g. paroxetine, omeprazole, fluconazole"
                className="w-full rounded-md bg-[#0d1117] border border-[#30363d] px-3 py-2.5 text-sm text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-[#2d8f61] transition-colors"
              />
              <p className="text-xs text-zinc-500 leading-relaxed">
                Comma-separated. Used for drug–drug–gene phenoconversion
                (e.g. paroxetine converts CYP2D6 normal metabolizers into
                poor metabolizers).
              </p>
            </div>

            {/* Error */}
            {error && (
              <div className="rounded-md bg-red-900/30 border border-red-700/50 px-4 py-3 text-sm text-red-400">
                {error}
              </div>
            )}

            {/* Upload progress */}
            {submitting && (
              <div
                className="rounded-md border border-[#1a6b4a]/40 bg-[#0d1117]/50 px-4 py-3"
                role="status"
                aria-live="polite"
              >
                <div className="mb-1.5 flex items-baseline justify-between text-xs text-zinc-300">
                  <span>
                    {uploadDone
                      ? "Starting analysis…"
                      : uploadFraction !== null
                        ? `Uploading… ${Math.round(uploadFraction * 100)}%`
                        : "Uploading…"}
                  </span>
                  <span className="font-mono text-zinc-500">
                    {formatBytes(uploadLoaded)}
                    {uploadTotal ? ` / ${formatBytes(uploadTotal)}` : ""}
                  </span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-zinc-800">
                  {uploadFraction === null || uploadDone ? (
                    // Indeterminate sweep while we wait for the server response
                    // (or when length isn't computable).
                    <div className="h-full w-1/3 animate-[upload-sweep_1.2s_ease-in-out_infinite] bg-[#2d8f61]" />
                  ) : (
                    <div
                      className="h-full bg-[#2d8f61] transition-[width] duration-150 ease-out"
                      style={{ width: `${Math.round(uploadFraction * 100)}%` }}
                    />
                  )}
                </div>
                <style jsx>{`
                  @keyframes upload-sweep {
                    0% {
                      transform: translateX(-100%);
                    }
                    100% {
                      transform: translateX(300%);
                    }
                  }
                `}</style>
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={!file || submitting}
              className="w-full rounded-lg bg-[#1a6b4a] text-white py-3.5 font-semibold text-sm disabled:opacity-40 disabled:cursor-not-allowed hover:bg-[#2d8f61] transition-colors shadow-lg shadow-[#1a6b4a]/20"
            >
              {submitting
                ? uploadDone
                  ? "Starting…"
                  : uploadFraction !== null
                    ? `Uploading ${Math.round(uploadFraction * 100)}%`
                    : "Uploading…"
                : "Analyze Variants"}
            </button>
          </form>

          {/* Privacy notice */}
          <p className="text-center text-xs text-zinc-500 mt-4">
            Genome files are encrypted in transit and at rest and are
            automatically deleted within 24 hours of job completion.
          </p>
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────────────────────────── */}
      <footer className="py-8 -mx-4 px-4 text-center space-y-2">
        <p
          className="text-sm text-[#3a3f4a]"
          style={{ fontFamily: "'DM Serif Display', serif" }}
        >
          PeptOdyssey
        </p>
        <p className="text-xs text-[#9ca3af]">
          Built by Florida Man Bioscience · v{versionData.version}
        </p>
      </footer>
    </div>
  );
}
