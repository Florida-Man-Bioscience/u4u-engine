import Link from "next/link";

/**
 * /tracking/model — formalization of the Bayesian model that produces the
 * per-biomarker posterior predictions and credible bands shown on the
 * patient charts.
 *
 * Server component, no client JS. The math mirrors the authoritative
 * implementation in engine/tracking/bayes.py + genetics.py exactly — if you
 * change the model there, update the equations here. Rendered with plain
 * styled HTML + an inline SVG (no KaTeX/MathJax dependency); Greek symbols
 * and operators are literal Unicode, matching the engine docstrings.
 */

const serif = { fontFamily: "'DM Serif Display', serif" };
const mono = { fontFamily: "'DM Mono', ui-monospace, monospace" };
const TEAL = "#0f766e";

export const metadata = {
  title: "Bayesian model — PeptOdyssey",
  description:
    "The Normal–Normal conjugate model behind the peptide → biomarker response predictions.",
};

export default function ModelPage() {
  return (
    <article className="space-y-10 text-slate-800">
      <header className="space-y-3">
        <p className="text-xs uppercase tracking-widest text-[#1a6b4a]">
          Methods · Biomarker tracking
        </p>
        <h1 className="text-4xl leading-tight" style={serif}>
          How the response prediction works
        </h1>
        <p className="max-w-3xl text-sm leading-relaxed text-slate-600">
          Every per-biomarker chart in the tracker shows a{" "}
          <strong>posterior prediction</strong>: a single trajectory with a 95%
          credible band, formed by combining what a patient&apos;s{" "}
          <em>genetics</em> predict (the prior) with what their{" "}
          <em>measurements</em> show (the likelihood). This page formalizes that
          model — the generative story, the conjugate update, and how
          uncertainty becomes the band you see. It mirrors the implementation in{" "}
          <code style={mono}>engine/tracking/bayes.py</code>,{" "}
          <code style={mono}>engine/tracking/genetics.py</code>, and{" "}
          <code style={mono}>engine/tracking/responder_index.py</code>.
        </p>
        <p className="max-w-3xl rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs leading-relaxed text-amber-900">
          Research / decision-support model — not a validated clinical
          predictor. It estimates the direction and rough magnitude of a
          response; it does not return a clinical result.
        </p>
      </header>

      {/* ── Data-flow diagram ─────────────────────────────────────────── */}
      <section className="space-y-3">
        <h2 className="text-2xl" style={serif}>
          The model at a glance
        </h2>
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white p-4">
          <FlowDiagram />
        </div>
        <p className="text-xs leading-relaxed text-slate-500">
          The prior is centred on the panel&apos;s documented effect and scaled
          by the patient&apos;s <em>responder index</em> <Sym>η</Sym> — a
          regularised linear index over a feature vector that generalises the old
          scalar responder strength <em>r</em> (today the genetics feature is the
          only one wired). Its width is sharpened or widened by the{" "}
          <Link href="/tracking/model#evidence" className="text-[#1a6b4a] underline">
            evidence grade
          </Link>{" "}
          of that biomarker. Measurements enter as one effective observation of
          the latent change θ. The two combine in closed form.
        </p>
      </section>

      {/* ── Latent quantity ───────────────────────────────────────────── */}
      <Section title="1 · The latent quantity">
        <p>
          For one <Tuple>patient, peptide, biomarker</Tuple> we model a single
          latent quantity <Sym>θ</Sym> — the fractional change from baseline once
          the peptide&apos;s effect has plateaued. <Sym>θ = 0.30</Sym> means
          &ldquo;this marker ends up +30% above baseline at steady state.&rdquo;
          The sign carries direction; the magnitude is the effect size.
        </p>
        <p>
          A measurement taken at week <Sym>w</Sym> hasn&apos;t reached steady
          state yet. The fraction of the asymptote reached by week{" "}
          <Sym>w</Sym> follows an exponential <em>approach curve</em> with a
          panel-derived time constant <Sym>τ</Sym>:
        </p>
        <Eq>a(w) = 1 − exp(−w / τ)</Eq>
        <p className="text-sm text-slate-600">
          So the expected value of the marker at week <Sym>w</Sym> is{" "}
          <Sym>baseline · (1 + θ · a(w))</Sym>: it starts at baseline (a(0)=0)
          and approaches <Sym>baseline · (1 + θ)</Sym> as <Sym>w → ∞</Sym>.
        </p>
      </Section>

      {/* ── Prior ─────────────────────────────────────────────────────── */}
      <Section title="2 · Prior — the responder index η">
        <p>
          Before any measurement, the prior on <Sym>θ</Sym> is Normal, centred on
          the panel&apos;s documented effect <Sym>θ̄</Sym> for that biomarker
          scaled by the patient&apos;s <strong>responder index</strong>{" "}
          <Sym>η</Sym> (centred at 1 = &ldquo;average responder&rdquo;):
        </p>
        <Eq>{`θ ~ Normal(μ₀, σ₀²)    with   μ₀ = η · θ̄`}</Eq>
        <p>
          <Sym>η</Sym> is the <strong>Hierarchical Bayesian Responder Index
          (HBRI)</strong>. It generalises the old scalar responder strength{" "}
          <Sym>r = 1 + 0.72 · tanh(w)</Sym> into a ridge-regularised linear index
          over a <em>feature vector</em> <Sym>x</Sym>, squashed by{" "}
          <Sym>tanh</Sym> to stay bounded in <Sym>[1 − Δ, 1 + Δ]</Sym> with{" "}
          <Sym>Δ = 0.72</Sym>:
        </p>
        <Eq>{`η = 1 + Δ · tanh(βᵀx)          Δ = 0.72`}</Eq>
        <p>
          The features come from auto-discovered <em>feature adapters</em>{" "}
          (<code style={mono}>engine/tracking/feature_adapters/</code>). The{" "}
          <strong>genetics feature is the anchored reference</strong>: it passes
          the patient&apos;s summed variant weight <Sym>w</Sym> through
          unstandardised with coefficient <Sym>β_g = 1</Sym>. So with genetics
          alone <Sym>βᵀx = w</Sym> and <Sym>η = 1 + Δ · tanh(w)</Sym> — the
          responder index <strong>reduces exactly to the prior scalar model</strong>,
          every number preserved.
        </p>
        <p>
          Other signals — a <Sym>PRS</Sym> inflammatory baseline, the{" "}
          <Sym>BPC-157</Sym> composite, coarse demographics, and HealthKit{" "}
          <em>behavioural</em> covariates (§6) — are additional features that
          enter the same linear index and thus shift the prior <em>mean</em>.
          Their coefficients carry a <strong>ridge prior</strong>{" "}
          <Sym>β_j ~ Normal(0, σ_β²)</Sym> that shrinks weakly-evidenced signals
          toward zero. Today the genetics adapter is the only one wired; the rest
          are framework slots with <Sym>β_j = 0</Sym>, so current predictions are
          genetics-only.
        </p>
        <p className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-600">
          <strong>Display-only signals.</strong> The receptor-isoform prediction
          and KEGG pathway overlays shown elsewhere in the app are{" "}
          <strong>not</strong> fused into this predictor — they inform{" "}
          <em>interpretation</em>, not <Sym>η</Sym>. Only registered feature
          adapters move the prior.
        </p>
        <p>
          Each feature carries a variance <Sym>var_j</Sym> on its value.
          Treating features as independent, that uncertainty propagates into a
          variance on the index itself by the <strong>delta method</strong>:
        </p>
        <Eq>{`Var(βᵀx) = Σⱼ βⱼ² · var_j`}</Eq>
        <Eq>{`dη/d(βᵀx) = Δ · sech²(βᵀx)`}</Eq>
        <Eq>{`Var(η) = ( Δ · sech²(βᵀx) )² · Var(βᵀx)`}</Eq>
        <p className="text-sm text-slate-600">
          The <Sym>sech²</Sym> factor is the slope of the <Sym>tanh</Sym> squash,
          so a confident feature far out on the flat tails barely moves{" "}
          <Sym>η</Sym> — a feature shifts the responder only as much as its
          certainty warrants. The genetics adapter engineers its <Sym>var_g</Sym>{" "}
          so that at the genetics-only operating point <Sym>βᵀx = w</Sym> this{" "}
          <Sym>Var(η)</Sym> reproduces the legacy responder SD exactly.
        </p>
        <p>
          The prior width then combines the index uncertainty{" "}
          <Sym>σ_η = √Var(η)</Sym> with the uncertainty in the panel effect
          itself, added in quadrature:
        </p>
        <Eq>{`σ₀ = √( (σ_η · |θ̄|)²  +  (ρ · |θ̄|)² )`}</Eq>
        <p className="text-sm text-slate-600">
          <Sym>ρ</Sym> is the <em>relative</em> uncertainty in the panel effect.
          For an uncited biomarker it is the flat default{" "}
          <Sym>ρ = 0.20</Sym>. For a biomarker with a curated, cited evidence
          entry it is the research-derived value — tighter when human RCTs back
          the effect, wider when only preclinical data do (see{" "}
          <a href="#evidence" className="text-[#1a6b4a] underline">
            evidence grades
          </a>
          ).
        </p>
      </Section>

      {/* ── Likelihood ────────────────────────────────────────────────── */}
      <Section title="3 · Likelihood — from measurements">
        <p>
          A patient&apos;s post-baseline measurements are summarised as one
          effective observation of <Sym>θ</Sym>. Each measurement{" "}
          <Sym>yᵢ</Sym> at week <Sym>wᵢ</Sym> is divided by its approach factor
          to estimate the asymptotic change, then the estimates are pooled by
          inverse variance. Baseline <Sym>b</Sym> and slope are fit jointly
          (a 2-parameter Bayesian linear regression in{" "}
          <Sym>b</Sym> and <Sym>φ = b·θ</Sym>) so the model recovers θ even when
          no pre-treatment sample exists:
        </p>
        <Eq>{`yᵢ = b + φ · a(wᵢ) + εᵢ ,   εᵢ ~ Normal(0, σ²)`}</Eq>
        <Eq>{`θ̂ = φ̂ / b̂      (delta-method variance → σ̄)`}</Eq>
        <p className="text-sm text-slate-600">
          With few measurements the slope&apos;s sampling distribution has
          Student-<em>t</em> tails, so <Sym>σ̄</Sym> is inflated by{" "}
          <Sym>t₀.₉₇₅(n−2) / z₀.₉₇₅</Sym> — without it the bands under-cover at
          small <Sym>n</Sym>.
        </p>
      </Section>

      {/* ── Posterior ─────────────────────────────────────────────────── */}
      <Section title="4 · Posterior — the conjugate update">
        <p>
          Normal prior × Normal likelihood is conjugate: the posterior on{" "}
          <Sym>θ</Sym> is again Normal, in closed form. Working in precision{" "}
          <Sym>τ = 1/σ²</Sym>:
        </p>
        <Eq>{`τ_post = τ_prior + τ_obs`}</Eq>
        <Eq>{`μ_post = (τ_prior · μ₀ + τ_obs · ȳ) / τ_post`}</Eq>
        <Eq>{`σ_post = √(1 / τ_post)`}</Eq>
        <p>
          The 95% <strong>credible interval</strong> on <Sym>θ</Sym> is then
          simply:
        </p>
        <Eq>{`[ μ_post − 1.96 · σ_post ,  μ_post + 1.96 · σ_post ]`}</Eq>
        <p className="text-sm text-slate-600">
          With no measurements the posterior equals the prior — which is exactly
          what a brand-new patient&apos;s chart shows: the prior prediction and
          its band, anchored on the panel&apos;s documented baseline.
        </p>
      </Section>

      {/* ── Posterior predictive ──────────────────────────────────────── */}
      <Section title="5 · Posterior predictive — the band you see">
        <p>
          Projecting the posterior on <Sym>θ</Sym> through the approach curve
          gives the predicted trajectory in measurement units, and propagating
          both <Sym>θ</Sym>- and baseline-uncertainty gives the 95% band:
        </p>
        <Eq>{`V(w) = b · (1 + μ_post · a(w))`}</Eq>
        <Eq>{`Var[V(w)] ≈ σ_b² · (1 + μ_post · a)²  +  b² · a² · σ_post²`}</Eq>
        <Eq>{`band(w) = V(w) ± 1.96 · √Var[V(w)]`}</Eq>
        <p className="text-sm text-slate-600">
          The <Sym>σ_b</Sym> term is dropped when a pre-treatment measurement
          pins the baseline directly (otherwise it double-counts uncertainty the
          delta-method already absorbed). The band is a point at <Sym>w = 0</Sym>{" "}
          (a(0)=0) and opens up as the effect accrues — the shape you see on the
          chart.
        </p>
      </Section>

      {/* ── HealthKit split by role ───────────────────────────────────── */}
      <Section title="6 · HealthKit — two roles, two sides of Bayes' rule">
        <p>
          HealthKit signals reach the model through a de-identified identity
          bridge (<code style={mono}>engine/tracking/healthkit_identity.py</code>).
          When wired, they split into <strong>two distinct roles</strong> that
          land on opposite sides of Bayes&apos; rule — conflating them would let a
          signal count twice:
        </p>
        <p>
          <strong>1 · Proxy observations.</strong> HealthKit quantities that{" "}
          <em>are</em> a tracked biomarker — resting heart rate, body mass,
          VO₂max — enter as additional <strong>likelihood</strong> observations{" "}
          <Sym>yᵢ</Sym> on <Sym>θ</Sym> (§3), under their own measurement-noise
          model. They update the posterior; they do <strong>not</strong> touch
          the prior.
        </p>
        <p>
          <strong>2 · Behavioural covariates.</strong> Signals that modulate{" "}
          <em>responsiveness</em> but are not the outcome — sleep, activity
          minutes, adherence proxies — enter as <strong>feature adapters</strong>{" "}
          contributing to <Sym>η</Sym> (the prior, §2), with ridge-shrunk{" "}
          <Sym>β_j</Sym> and honest <Sym>var_j</Sym>.
        </p>
        <p className="text-sm text-slate-600">
          Keeping a covariate on the prior side and a proxy measurement on the
          likelihood side prevents a covariate from being double-counted as
          evidence of the very effect it predicts.
        </p>
      </Section>

      {/* ── Gated-later extensions ────────────────────────────────────── */}
      <Section title="7 · Gated-later extensions">
        <p>
          Two generalisations are specified but deliberately <strong>gated</strong>{" "}
          — not wired into the predictor until the modelling and data support
          them:
        </p>
        <p>
          <strong>Cross-biomarker covariance over a shared <Sym>η</Sym>.</strong>{" "}
          Multiple biomarkers for one <Tuple>patient, peptide</Tuple> share the
          same responder index. Modelling them jointly with a covariance over the
          shared <Sym>η</Sym> would let a strong signal in one marker inform
          another — but it needs a multivariate prior and careful
          identifiability work.
        </p>
        <p>
          <strong>Dose-response.</strong> Replacing <Sym>θ</Sym> with an
          effective <Sym>θ_eff = θ · s(dose)</Sym> for a saturating dose function{" "}
          <Sym>s</Sym> — gated behind dose-stratified data the cohort does not
          yet have.
        </p>
      </Section>

      {/* ── Calibration ───────────────────────────────────────────────── */}
      <Section title="8 · Is the band honest?">
        <p>
          A 95% band should contain the truth 95% of the time. That is a
          testable claim, and it is tested: a Monte-Carlo backtest
          (<code style={mono}>tests/…/test_calibration.py</code>) draws true{" "}
          <Sym>(baseline, θ)</Sym>, simulates noisy measurements, and checks
          empirical coverage in four regimes (pre-baseline ✓/✗ × low/high
          noise). Coverage is held within <Sym>[0.90, 0.995]</Sym>; the model is
          tuned to stay just inside the conservative edge rather than
          over-claim precision.
        </p>
      </Section>

      {/* ── Evidence grades ───────────────────────────────────────────── */}
      <section id="evidence" className="space-y-3 scroll-mt-20">
        <h2 className="text-2xl" style={serif}>
          9 · Evidence grades feed the prior width
        </h2>
        <p className="max-w-3xl text-sm leading-relaxed text-slate-600">
          The panel-effect uncertainty <Sym>ρ</Sym> in step 2 is research-driven.
          A curated registry (
          <code style={mono}>data/biomarker_evidence.json</code>) records, per
          biomarker, the documented effect, its citations, and an evidence
          grade. The grade sets a tighter or wider <Sym>ρ</Sym> than the flat
          0.20 default, so the prior is as confident as the literature warrants —
          no more:
        </p>
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-slate-500">
                <Th>Grade</Th>
                <Th>Evidence</Th>
                <Th>
                  Relative SD <span style={mono}>ρ</span>
                </Th>
                <Th>Effect on the prior</Th>
              </tr>
            </thead>
            <tbody>
              <GradeRow g="A" ev="Multiple human RCTs / meta-analysis" sd="0.10" note="Tightest — band leans on strong human data" />
              <GradeRow g="B" ev="≥1 human RCT; magnitude class-approximate" sd="0.15" note="Tighter than default (e.g. tesamorelin → IGF-1)" />
              <GradeRow g="C" ev="Human observational / open-label / mechanistic" sd="0.22" note="Slightly wider than default" />
              <GradeRow g="D" ev="Preclinical only (animal / in vitro)" sd="0.30" note="Honestly wider (e.g. BPC-157 → VEGF)" />
              <GradeRow g="—" ev="Uncited (most of the panel today)" sd="0.20" note="Legacy flat default; unchanged behaviour" uncited />
            </tbody>
          </table>
        </div>
        <p className="text-xs leading-relaxed text-slate-500">
          The registry is updated through a curator CLI
          (<code style={mono}>python -m engine.tracking.evidence_update</code>),
          which refuses to record an entry without a real, retrieved citation —
          the model never invents provenance to look more certain than it is.
        </p>
      </section>

      <footer className="border-t border-slate-200 pt-6">
        <Link
          href="/tracking"
          className="text-sm text-[#1a6b4a] underline underline-offset-2"
        >
          ← Back to biomarker tracking
        </Link>
      </footer>
    </article>
  );
}

/* ── Helper components ─────────────────────────────────────────────────── */

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-3">
      <h2 className="text-2xl" style={serif}>
        {title}
      </h2>
      <div className="max-w-3xl space-y-3 text-sm leading-relaxed text-slate-700">
        {children}
      </div>
    </section>
  );
}

function Eq({ children }: { children: React.ReactNode }) {
  return (
    <div
      className="my-2 overflow-x-auto rounded-md border border-slate-200 bg-slate-50 px-4 py-2.5 text-[15px] text-slate-900"
      style={{ fontFamily: "'DM Mono', ui-monospace, monospace" }}
    >
      {children}
    </div>
  );
}

function Sym({ children }: { children: React.ReactNode }) {
  return (
    <span style={{ fontFamily: "'DM Mono', ui-monospace, monospace" }} className="text-[#0f766e]">
      {children}
    </span>
  );
}

function Tuple({ children }: { children: React.ReactNode }) {
  return <span className="italic text-slate-600">⟨{children}⟩</span>;
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="px-4 py-2 font-medium">{children}</th>;
}

function GradeRow({
  g,
  ev,
  sd,
  note,
  uncited,
}: {
  g: string;
  ev: string;
  sd: string;
  note: string;
  uncited?: boolean;
}) {
  return (
    <tr className={`border-b border-slate-100 ${uncited ? "text-slate-500" : ""}`}>
      <td className="px-4 py-2">
        <span
          className="inline-flex h-6 w-6 items-center justify-center rounded-full text-xs font-semibold"
          style={{
            backgroundColor: uncited ? "#e2e8f0" : "#0f766e",
            color: uncited ? "#475569" : "white",
          }}
        >
          {g}
        </span>
      </td>
      <td className="px-4 py-2">{ev}</td>
      <td className="px-4 py-2" style={{ fontFamily: "'DM Mono', ui-monospace, monospace" }}>
        {sd}
      </td>
      <td className="px-4 py-2 text-slate-600">{note}</td>
    </tr>
  );
}

/* ── Inline SVG data-flow diagram ──────────────────────────────────────── */

function FlowDiagram() {
  return (
    <svg
      viewBox="0 0 760 260"
      className="mx-auto block h-auto w-full max-w-3xl"
      role="img"
      aria-label="Data-flow: a feature-vector responder index and evidence form a prior; measurements form a likelihood; together they yield a posterior and a predictive band."
    >
      <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 z" fill="#94a3b8" />
        </marker>
      </defs>

      {/* Inputs */}
      <Node x={10} y={20} w={170} h={46} title="Feature vector x" sub="responder index η" />
      <Node x={10} y={78} w={170} h={46} title="Evidence registry" sub="grade → ρ (prior width)" accent />
      <Node x={10} y={170} w={170} h={46} title="Measurements" sub="y(w) over time" />

      {/* Prior + Likelihood */}
      <Node x={250} y={48} w={160} h={52} title="Prior" sub="θ ~ N(μ₀, σ₀²)" />
      <Node x={250} y={168} w={160} h={52} title="Likelihood" sub="θ̄, σ̄ (one obs.)" />

      {/* Posterior */}
      <Node x={480} y={108} w={150} h={52} title="Posterior" sub="θ ~ N(μ*, σ*²)" strong />

      {/* Predictive */}
      <Node x={660} y={108} w={90} h={52} title="Predict" sub="V(w) ± band" strong />

      {/* Arrows */}
      <Edge x1={180} y1={43} x2={250} y2={66} />
      <Edge x1={180} y1={101} x2={250} y2={80} />
      <Edge x1={180} y1={193} x2={250} y2={194} />
      <Edge x1={410} y1={74} x2={480} y2={124} />
      <Edge x1={410} y1={194} x2={480} y2={144} />
      <Edge x1={630} y1={134} x2={660} y2={134} />

      {/* combine glyph */}
      <text x={455} y={138} fontSize="20" fill="#0f766e" textAnchor="middle" fontFamily="'DM Mono', monospace">⊕</text>
    </svg>
  );
}

function Node({
  x,
  y,
  w,
  h,
  title,
  sub,
  accent,
  strong,
}: {
  x: number;
  y: number;
  w: number;
  h: number;
  title: string;
  sub: string;
  accent?: boolean;
  strong?: boolean;
}) {
  const stroke = strong ? "#0f766e" : accent ? "#1a6b4a" : "#cbd5e1";
  const fill = strong ? "#ecfdf5" : accent ? "#f0fdf4" : "#ffffff";
  return (
    <g>
      <rect
        x={x}
        y={y}
        width={w}
        height={h}
        rx={8}
        fill={fill}
        stroke={stroke}
        strokeWidth={strong ? 2 : 1.25}
      />
      <text x={x + 12} y={y + 20} fontSize="13" fill="#0f172a" fontFamily="'DM Serif Display', serif">
        {title}
      </text>
      <text x={x + 12} y={y + 37} fontSize="11" fill="#475569" fontFamily="'DM Mono', monospace">
        {sub}
      </text>
    </g>
  );
}

function Edge({ x1, y1, x2, y2 }: { x1: number; y1: number; x2: number; y2: number }) {
  return (
    <line
      x1={x1}
      y1={y1}
      x2={x2}
      y2={y2}
      stroke="#94a3b8"
      strokeWidth={1.5}
      markerEnd="url(#arrow)"
    />
  );
}
