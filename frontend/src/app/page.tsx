"use client";

import { useCallback, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { analyzeFile } from "./lib/api";
import versionData from "../../version.json";

const ACCEPTED = ".vcf,.txt,.csv";
const MAX_SIZE_MB = 100;

const HERO_STATS = [
  { value: "20+", label: "Peptide therapies" },
  { value: "7", label: "Annotation engines" },
  { value: "81", label: "ACMG actionable genes" },
  { value: "A–D", label: "Graded evidence priors" },
];

const PIPELINE_STEPS = [
  {
    icon: "01",
    title: "Upload",
    desc: "Drop your genome file — VCF, 23andMe, or CSV. Encrypted in transit and at rest.",
  },
  {
    icon: "02",
    title: "Annotate",
    desc: "Cross-referenced against ClinVar, gnomAD, VEP, UniProt, PharmGKB, and GWAS Catalog.",
  },
  {
    icon: "03",
    title: "Predict",
    desc: "Bayesian peptide-response modeling from pathway, receptor, and pharmacogenomic signals.",
  },
  {
    icon: "04",
    title: "Report",
    desc: "Clinically prioritized variants with per-peptide gene mapping and 95% credible intervals.",
  },
];

const PEPTIDE_HIGHLIGHTS = [
  { name: "Semaglutide / GLP-1", category: "Metabolic · Incretin", grade: "A" },
  { name: "BPC-157", category: "Multi-Pathway Regenerative", grade: "D" },
  { name: "Thymosin Alpha-1", category: "Immune Modulation", grade: "C" },
  { name: "CJC-1295 + Ipamorelin", category: "Growth Hormone Axis", grade: "B" },
  { name: "Tesamorelin", category: "GH / Body Composition", grade: "B" },
  { name: "Tirzepatide", category: "Dual GIP/GLP-1", grade: "A" },
  { name: "MOTS-c", category: "Mitochondrial / Metabolic", grade: "—" },
  { name: "Epithalon", category: "Longevity / Telomere", grade: "—" },
];

const ENGINES = [
  "Ensembl VEP",
  "NCBI ClinVar",
  "gnomAD",
  "MyVariant.info",
  "UniProt",
  "PharmGKB",
  "GWAS Catalog",
];

const GRADE_TONE: Record<string, string> = {
  A: "bg-emerald-400/15 text-emerald-300 border-emerald-400/30",
  B: "bg-teal-400/15 text-teal-300 border-teal-400/30",
  C: "bg-cyan-400/15 text-cyan-300 border-cyan-400/30",
  D: "bg-zinc-400/10 text-zinc-400 border-zinc-500/30",
  "—": "bg-zinc-400/10 text-zinc-500 border-zinc-600/30",
};

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

  const serif = { fontFamily: "'DM Serif Display', serif" };

  return (
    <div className="space-y-0">
      {/* ── Hero ────────────────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden bg-[#08090d] -mx-4 -mt-8 px-4 pt-24 pb-28">
        {/* Animated aurora field */}
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div className="hero-aurora absolute -top-1/3 left-1/2 h-[700px] w-[900px] -translate-x-1/2 rounded-full bg-[radial-gradient(closest-side,rgba(45,143,97,0.35),transparent)] blur-[100px]" />
          <div className="hero-aurora-2 absolute top-1/4 -right-40 h-[460px] w-[460px] rounded-full bg-[radial-gradient(closest-side,rgba(20,184,166,0.28),transparent)] blur-[90px]" />
          <div className="hero-aurora-3 absolute -bottom-40 -left-32 h-[520px] w-[520px] rounded-full bg-[radial-gradient(closest-side,rgba(34,211,238,0.18),transparent)] blur-[110px]" />
        </div>
        {/* Fine grid */}
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.05]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,.6) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.6) 1px, transparent 1px)",
            backgroundSize: "56px 56px",
            maskImage:
              "radial-gradient(ellipse 70% 60% at 50% 35%, #000 40%, transparent 100%)",
          }}
        />

        <div className="relative mx-auto max-w-3xl text-center">
          <div className="fade-up inline-flex items-center gap-2 rounded-full border border-[#2d8f61]/40 bg-[#2d8f61]/10 px-4 py-1.5 text-xs font-medium uppercase tracking-[0.18em] text-[#5fd6a0] backdrop-blur">
            <span className="relative flex h-1.5 w-1.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#5fd6a0] opacity-75" />
              <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-[#5fd6a0]" />
            </span>
            Precision Peptide Genomics
          </div>

          <h1
            className="fade-up fade-up-1 mt-7 text-5xl leading-[1.05] tracking-tight text-white sm:text-7xl"
            style={serif}
          >
            Your Genome.
            <br />
            <span className="bg-gradient-to-r from-[#5fd6a0] via-[#2dd4bf] to-[#22d3ee] bg-clip-text text-transparent">
              Your Peptide Map.
            </span>
          </h1>

          <p className="fade-up fade-up-2 mx-auto mt-6 max-w-xl text-lg leading-relaxed text-zinc-400">
            Upload your genetic data and see which peptide therapies align with
            your biology — variant-level analysis with Bayesian, evidence-graded
            response prediction across a growing peptide panel.
          </p>

          <div className="fade-up fade-up-3 mt-9 flex flex-wrap items-center justify-center gap-3">
            <a
              href="#upload"
              className="group relative inline-flex items-center gap-2 overflow-hidden rounded-xl bg-gradient-to-r from-[#1a6b4a] to-[#2d8f61] px-8 py-3.5 text-sm font-semibold text-white shadow-[0_8px_30px_-6px_rgba(45,143,97,0.6)] transition-all hover:shadow-[0_10px_40px_-4px_rgba(45,143,97,0.8)] hover:-translate-y-0.5"
            >
              <span className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/25 to-transparent transition-transform duration-700 group-hover:translate-x-full" />
              Start Analysis
              <span className="text-lg leading-none transition-transform group-hover:translate-x-0.5">
                &#x2192;
              </span>
            </a>
            <a
              href="#how"
              className="inline-flex items-center gap-2 rounded-xl border border-white/15 bg-white/5 px-7 py-3.5 text-sm font-semibold text-zinc-200 backdrop-blur transition-colors hover:border-white/30 hover:bg-white/10"
            >
              How it works
            </a>
          </div>

          {/* Stat strip */}
          <div className="fade-up fade-up-4 mx-auto mt-14 grid max-w-2xl grid-cols-2 gap-px overflow-hidden rounded-2xl border border-white/10 bg-white/5 backdrop-blur sm:grid-cols-4">
            {HERO_STATS.map((s) => (
              <div key={s.label} className="bg-[#0d1117]/40 px-4 py-5">
                <div
                  className="bg-gradient-to-b from-white to-zinc-400 bg-clip-text text-2xl text-transparent sm:text-3xl"
                  style={serif}
                >
                  {s.value}
                </div>
                <div className="mt-1 text-[11px] uppercase tracking-wide text-zinc-500">
                  {s.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Engines marquee ─────────────────────────────────────────────────── */}
      <section className="-mx-4 overflow-hidden border-y border-[#dbd9d3] bg-white px-4 py-5">
        <div className="mx-auto flex max-w-5xl items-center gap-6">
          <span className="shrink-0 text-[11px] font-semibold uppercase tracking-[0.16em] text-[#9ca3af]">
            Powered by
          </span>
          <div className="relative flex-1 overflow-hidden [mask-image:linear-gradient(90deg,transparent,#000_8%,#000_92%,transparent)]">
            <div className="marquee flex w-max items-center gap-3">
              {[...ENGINES, ...ENGINES].map((engine, i) => (
                <span
                  key={`${engine}-${i}`}
                  className="inline-flex shrink-0 items-center rounded-full border border-[#e4e2dd] bg-[#f7f6f3] px-4 py-1.5 text-sm font-medium text-[#3a3f4a]"
                >
                  {engine}
                </span>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── How it works ────────────────────────────────────────────────────── */}
      <section id="how" className="-mx-4 px-4 py-20">
        <div className="mx-auto max-w-5xl">
          <div className="mb-12 text-center">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#2d8f61]">
              The Pipeline
            </p>
            <h2 className="mt-2 text-3xl text-[#0d1117]" style={serif}>
              From raw genome to peptide map
            </h2>
          </div>
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {PIPELINE_STEPS.map((step, i) => (
              <div
                key={step.icon}
                className="group fade-up relative rounded-2xl bg-gradient-to-b from-[#e9e7e1] to-transparent p-px transition-transform hover:-translate-y-1"
                style={{ animationDelay: `${i * 80}ms` }}
              >
                <div className="relative h-full overflow-hidden rounded-2xl bg-white p-6">
                  <div className="absolute -right-6 -top-6 h-20 w-20 rounded-full bg-[#1a6b4a]/0 blur-2xl transition-all duration-500 group-hover:bg-[#2d8f61]/20" />
                  <span
                    className="bg-gradient-to-br from-[#1a6b4a] to-[#2dd4bf] bg-clip-text text-3xl text-transparent"
                    style={serif}
                  >
                    {step.icon}
                  </span>
                  <h3 className="mt-3 text-sm font-semibold text-[#0d1117]">
                    {step.title}
                  </h3>
                  <p className="mt-1.5 text-xs leading-relaxed text-[#6b7280]">
                    {step.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Peptide Therapy Coverage ────────────────────────────────────────── */}
      <section className="relative -mx-4 overflow-hidden border-y border-[#1a6b4a]/20 bg-[#0b0d12] px-4 py-20">
        <div className="pointer-events-none absolute left-1/2 top-0 h-72 w-[700px] -translate-x-1/2 rounded-full bg-[#1a6b4a]/15 blur-[120px]" />
        <div className="relative mx-auto max-w-5xl">
          <div className="mb-12 text-center">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#5fd6a0]">
              Coverage
            </p>
            <h2 className="mt-2 text-3xl text-white" style={serif}>
              Peptides, mapped to your genes
            </h2>
            <p className="mx-auto mt-3 max-w-lg text-sm text-zinc-400">
              Each therapy is matched to its target genes and scored against your
              variants — graded A–D by the strength of the underlying evidence.
            </p>
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {PEPTIDE_HIGHLIGHTS.map((p, i) => (
              <div
                key={p.name}
                className="group fade-up relative overflow-hidden rounded-xl border border-white/10 bg-white/[0.03] p-4 transition-all hover:border-[#2d8f61]/40 hover:bg-white/[0.06]"
                style={{ animationDelay: `${i * 50}ms` }}
              >
                <div className="absolute inset-x-0 -top-px h-px bg-gradient-to-r from-transparent via-[#2d8f61]/60 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm font-semibold text-white">{p.name}</p>
                  <span
                    className={`shrink-0 rounded-md border px-1.5 py-0.5 text-[10px] font-bold ${GRADE_TONE[p.grade] ?? GRADE_TONE["—"]}`}
                    title="Evidence grade"
                  >
                    {p.grade}
                  </span>
                </div>
                <p className="mt-1 text-xs text-zinc-400">{p.category}</p>
              </div>
            ))}
          </div>
          <p className="mt-6 text-center text-xs text-zinc-500">
            …plus Liraglutide, TB-500, GHK-Cu, AOD-9604, Thymosin Beta-4, and
            combination protocols. Evidence grades reflect human-RCT depth.
          </p>
        </div>
      </section>

      {/* ── Upload form ─────────────────────────────────────────────────────── */}
      <section
        id="upload"
        className="relative -mx-4 overflow-hidden bg-[#08090d] px-4 py-20"
      >
        <div className="pointer-events-none absolute left-1/2 top-1/4 h-[400px] w-[600px] -translate-x-1/2 rounded-full bg-[#1a6b4a]/15 blur-[120px]" />
        <div className="relative mx-auto max-w-xl">
          <div className="mb-8 text-center">
            <h2 className="text-3xl text-white" style={serif}>
              Begin your analysis
            </h2>
            <p className="mt-2 text-sm text-zinc-400">
              Upload a genome file to generate your personalized peptide therapy
              report.
            </p>
          </div>

          {/* Glass card */}
          <div className="rounded-2xl bg-gradient-to-b from-[#2d8f61]/30 to-white/5 p-px shadow-[0_20px_60px_-20px_rgba(45,143,97,0.4)]">
            <form
              onSubmit={handleSubmit}
              className="space-y-5 rounded-2xl bg-[#10141b]/90 p-6 backdrop-blur"
            >
              {/* Drop zone */}
              <div
                role="button"
                tabIndex={0}
                aria-label="File drop zone"
                className={`flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-10 transition-all ${
                  dragging
                    ? "scale-[1.01] border-[#2d8f61] bg-[#1a6b4a]/15"
                    : file
                      ? "border-[#2d8f61] bg-[#1a6b4a]/10"
                      : "cursor-pointer border-[#30363d] hover:border-[#2d8f61]/60 hover:bg-[#1a6b4a]/5"
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
                    <span className="mb-2 text-4xl text-[#2d8f61]">&#x2714;</span>
                    <p className="font-medium text-[#5fd6a0]">{file.name}</p>
                    <p className="mt-1 text-xs text-zinc-500">
                      {(file.size / 1024 / 1024).toFixed(2)} MB — click to change
                    </p>
                  </>
                ) : (
                  <>
                    <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-[#1a6b4a]/30 to-[#2dd4bf]/20 ring-1 ring-inset ring-[#2d8f61]/30">
                      <span className="text-2xl text-[#5fd6a0]">&#x2191;</span>
                    </div>
                    <p className="font-medium text-zinc-200">
                      Drag &amp; drop or click to choose
                    </p>
                    <p className="mt-1 text-xs text-zinc-500">
                      .vcf, .txt, .csv — max {MAX_SIZE_MB} MB
                    </p>
                  </>
                )}
              </div>

              {/* Current medications (optional) — drives DDGI phenoconversion */}
              <div className="space-y-1.5">
                <label
                  htmlFor="medications"
                  className="block text-xs font-semibold uppercase tracking-wide text-zinc-300"
                >
                  Current Medications{" "}
                  <span className="font-normal normal-case tracking-normal text-zinc-500">
                    — optional
                  </span>
                </label>
                <input
                  id="medications"
                  type="text"
                  value={medications}
                  onChange={(e) => setMedications(e.target.value)}
                  placeholder="e.g. paroxetine, omeprazole, fluconazole"
                  className="w-full rounded-md border border-[#30363d] bg-[#0d1117] px-3 py-2.5 text-sm text-zinc-200 transition-colors placeholder:text-zinc-600 focus:border-[#2d8f61] focus:outline-none focus:ring-1 focus:ring-[#2d8f61]/40"
                />
                <p className="text-xs leading-relaxed text-zinc-500">
                  Comma-separated. Used for drug–drug–gene phenoconversion (e.g.
                  paroxetine converts CYP2D6 normal metabolizers into poor
                  metabolizers).
                </p>
              </div>

              {/* Error */}
              {error && (
                <div className="rounded-md border border-red-700/50 bg-red-900/30 px-4 py-3 text-sm text-red-400">
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
                      <div className="h-full w-1/3 animate-[upload-sweep_1.2s_ease-in-out_infinite] bg-gradient-to-r from-[#1a6b4a] to-[#2dd4bf]" />
                    ) : (
                      <div
                        className="h-full bg-gradient-to-r from-[#1a6b4a] to-[#2dd4bf] transition-[width] duration-150 ease-out"
                        style={{ width: `${Math.round(uploadFraction * 100)}%` }}
                      />
                    )}
                  </div>
                </div>
              )}

              {/* Submit */}
              <button
                type="submit"
                disabled={!file || submitting}
                className="group relative w-full overflow-hidden rounded-xl bg-gradient-to-r from-[#1a6b4a] to-[#2d8f61] py-3.5 text-sm font-semibold text-white shadow-lg shadow-[#1a6b4a]/20 transition-all hover:-translate-y-0.5 hover:shadow-[0_10px_30px_-6px_rgba(45,143,97,0.7)] disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:translate-y-0"
              >
                {!submitting && (
                  <span className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/25 to-transparent transition-transform duration-700 group-hover:translate-x-full" />
                )}
                {submitting
                  ? uploadDone
                    ? "Starting…"
                    : uploadFraction !== null
                      ? `Uploading ${Math.round(uploadFraction * 100)}%`
                      : "Uploading…"
                  : "Analyze Variants"}
              </button>
            </form>
          </div>

          {/* Privacy notice */}
          <p className="mx-auto mt-5 flex items-center justify-center gap-1.5 text-center text-xs text-zinc-500">
            <span className="text-[#2d8f61]">&#x1F512;</span>
            Encrypted in transit and at rest · auto-deleted within 24h of
            completion.
          </p>
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────────────────────────── */}
      <footer className="-mx-4 space-y-2 px-4 py-10 text-center">
        <p className="text-sm text-[#3a3f4a]" style={serif}>
          PeptOdyssey
        </p>
        <p className="text-xs text-[#9ca3af]">
          Built by Florida Man Bioscience · v{versionData.version}
        </p>
      </footer>

      {/* ── Animations ──────────────────────────────────────────────────────── */}
      <style jsx global>{`
        @keyframes upload-sweep {
          0% {
            transform: translateX(-100%);
          }
          100% {
            transform: translateX(300%);
          }
        }
        @keyframes fade-up {
          from {
            opacity: 0;
            transform: translateY(16px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .fade-up {
          animation: fade-up 0.7s cubic-bezier(0.16, 1, 0.3, 1) both;
        }
        .fade-up-1 {
          animation-delay: 0.08s;
        }
        .fade-up-2 {
          animation-delay: 0.16s;
        }
        .fade-up-3 {
          animation-delay: 0.24s;
        }
        .fade-up-4 {
          animation-delay: 0.32s;
        }
        @keyframes aurora-drift {
          0%,
          100% {
            transform: translate(-50%, 0) scale(1);
            opacity: 0.9;
          }
          50% {
            transform: translate(-50%, 24px) scale(1.08);
            opacity: 1;
          }
        }
        @keyframes aurora-drift-2 {
          0%,
          100% {
            transform: translate(0, 0) scale(1);
          }
          50% {
            transform: translate(-30px, 30px) scale(1.1);
          }
        }
        @keyframes aurora-drift-3 {
          0%,
          100% {
            transform: translate(0, 0) scale(1);
          }
          50% {
            transform: translate(30px, -20px) scale(1.12);
          }
        }
        .hero-aurora {
          animation: aurora-drift 14s ease-in-out infinite;
        }
        .hero-aurora-2 {
          animation: aurora-drift-2 18s ease-in-out infinite;
        }
        .hero-aurora-3 {
          animation: aurora-drift-3 16s ease-in-out infinite;
        }
        @keyframes marquee {
          from {
            transform: translateX(0);
          }
          to {
            transform: translateX(-50%);
          }
        }
        .marquee {
          animation: marquee 26s linear infinite;
        }
        @media (prefers-reduced-motion: reduce) {
          .fade-up,
          .hero-aurora,
          .hero-aurora-2,
          .hero-aurora-3,
          .marquee {
            animation: none !important;
          }
          .fade-up {
            opacity: 1;
          }
        }
      `}</style>
    </div>
  );
}
