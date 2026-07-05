# Unified Peptide-Response Model — Formal Spec

> **Status: research / decision-support, NOT a validated clinical predictor.**
> This document specifies a Bayesian model used to *aid interpretation* of
> longitudinal biomarker data under peptide therapy. It is not a diagnostic
> device and produces no clinical determination. All effect magnitudes are
> informal or grade-tagged research estimates (see
> `engine/tracking/evidence.py`); credible intervals describe model belief,
> not guaranteed coverage of a patient's true response.

This is **Phase 0** — the behaviour-preserving foundation. The generative
model below is exactly what `engine/tracking/` computes today; the
**Hierarchical Bayesian Responder Index (HBRI)** generalisation is wired in
such that, with only the genetics feature present, every number is identical
to the pre-refactor model (enforced by
`tests/test_engine/test_tracking/test_responder_index.py`).

---

## 1. Generative model (per patient `p`, peptide, biomarker `k`)

Latent quantity **θ** = fractional change from baseline at plateau. e.g.
θ = 0.30 means "+30 % above baseline once the effect plateaus."

**Prior** (from genetics; §2 generalises this):

$$\theta \sim \mathcal{N}(\mu_0,\ \sigma_0^2),\qquad \mu_0 = \eta \cdot \text{expected\_pct}_k$$

**Kinetics** — expected approach curve with panel-derived time constant τ:

$$a(w) = 1 - e^{-w/\tau}\quad(\text{weeks } w\ge 0)$$

**Likelihood** — each post-baseline measurement `y_i` at week `w_i`:

$$y_i \mid b,\theta = b\,(1 + \theta\, a(w_i)) + \varepsilon_i,\qquad \varepsilon_i \sim \mathcal{N}(0,\sigma^2)$$

Baseline `b` and θ are fit **jointly** (reparameterised as a linear regression
in `(b, φ)` with `φ = b·θ`), with an informative prior on `b` (the panel's
documented physiologic baseline) and a near-flat prior on the slope. The
likelihood on θ is recovered by the delta method, with a Student-t inflation on
σ_θ for small `n`. See `engine/tracking/bayes.py::joint_fit_likelihood`.

**Conjugate update** (Normal–Normal):

$$\tau_{\text{post}} = \tau_{\text{prior}} + \tau_{\text{obs}},\qquad
\mu_{\text{post}} = \frac{\tau_{\text{prior}}\mu_{\text{prior}} + \tau_{\text{obs}}\bar y}{\tau_{\text{post}}}$$

**Posterior predictive** at week `w`:

$$V(w) = b\,(1 + \mu_{\text{post}}\, a(w)),\qquad
\operatorname{Var}(V) \approx \sigma_b^2 (1+\mu a)^2 + b^2 a^2 \sigma_\theta^2$$

---

## 2. The η generalisation (HBRI)

The legacy prior mean used a scalar *responder strength*
`r = 1 + Δ·tanh(w)`, where `w` is the patient's summed genetic weight for the
peptide and `Δ = R_DELTA_SCALE = 0.72`. HBRI replaces the scalar `w` with a
regularised linear index over a **feature vector**:

$$\eta_{p,k} = 1 + \Delta\cdot\tanh(\beta^\top x_{p,k}),\qquad \eta \in [1-\Delta,\ 1+\Delta]$$

- `x` = standardised features assembled from registered **feature adapters**
  (`engine/tracking/feature_adapters/`, auto-discovered via `pkgutil`).
- The **genetics feature** is the anchored reference: value `x_g = w`,
  coefficient **`β_g = 1`** (not shrunk, not standardised — it passes `w`
  through). With genetics alone, `β^⊤x = w` and `η = 1 + Δ·tanh(w)` exactly.
- **Non-genetic** coefficients get a **ridge prior** `β_j ~ N(0, σ_β²)` and are
  **defaulted to 0** in this PR (no other adapters exist yet). Adding one is a
  single new file in `feature_adapters/` — zero edits to shared modules.

### 2.1 Feature-uncertainty propagation (delta method)

Each feature carries a variance `var_j` on its value. Treating features as
independent:

$$\operatorname{Var}(\beta^\top x) = \sum_j \beta_j^2\, \text{var}_j$$

$$\frac{d\eta}{d(\beta^\top x)} = \Delta\,\operatorname{sech}^2(\beta^\top x),\qquad
\boxed{\ \operatorname{Var}(\eta) = \big(\Delta\,\operatorname{sech}^2(\beta^\top x)\big)^2 \cdot \operatorname{Var}(\beta^\top x)\ }$$

So a feature moves the responder mean only as much as its certainty warrants.

### 2.2 Backward-compat contract (frozen)

The legacy responder SD is a heuristic that shrinks with the number of relevant
variants `n`:

$$\text{today\_sd} = \max\big(R_{\min},\ R_{\text{base}}/\sqrt{1 + 0.5 n}\big)$$

To reproduce it exactly, the genetics adapter reports a **feature-space
variance** engineered so the delta method closes the loop at the genetics-only
operating point `L = w`:

$$\text{var}_g = \frac{\text{today\_sd}^2}{\big(\Delta\,\operatorname{sech}^2(w)\big)^2}
\ \Longrightarrow\
\operatorname{Var}(\eta)\big|_{\text{genetics only}} = \big(\Delta\,\operatorname{sech}^2(w)\big)^2\,\text{var}_g = \text{today\_sd}^2.$$

Both sides use the **same shared slope helper** `_deta_dlinear`, so the
cancellation is against the identical float (it is *not* bit-exact under IEEE
754 — the golden test compares with an absolute tolerance, never `==`).

### 2.3 Frozen composition rule for Phase 1

**Decision (must not silently change once other adapters ship):** when
non-genetic features shift the operating point to `L ≠ w`, the genetics
contribution to `Var(η)` **re-evaluates at the shifted `L`** — i.e. the index
computes `Var(η) = (Δ·sech²(L))² · Σ_j β_j² var_j` using the *global* `L`, and
`var_g` stays pinned at the value backed out at `L = w`. Consequences:

- Genetics-only (`L = w`): reproduces `today_sd²` exactly (the contract above).
- With other features: the genetics variance is propagated at the true joint
  operating point, which is the mathematically correct delta-method behaviour —
  adding information legitimately changes where we linearise. The genetics
  contribution is therefore **not** re-pinned to `today_sd²` off-operating-point.

This is the single load-bearing interface decision for the fan-out; adapters
must not assume their contribution is evaluated in isolation.

---

## 3. Double-counting mitigation (genetics × cohort)

`combine_priors` (`engine/tracking/pooling.py`) fuses the genetic prior with an
empirical-Bayes **population prior** (leave-one-out donor cohort) by adding
precisions `τ_g + τ_p`, treating them as independent. They are not: a cohort's
observed response is itself partly driven by genetics, so the summed precision
overstates information. The redundancy is negligible for the genetics-only
scalar prior but grows with a rich feature vector fused against a real cohort.

**Cap.** `cap_combined_precision` bounds the fused precision:

$$\tau_{\text{combined}} \le \text{CAP\_MULT}\cdot\max(\tau_g, \tau_p),\qquad \text{CAP\_MULT}=2.0$$

**Gate (critical).** The cap is applied in `predict_response` **only when**
*(≥1 non-genetic feature)* **AND** *(≥ `MIN_DONORS` donors)* are both present.
Genetics-only — today's default, at *any* donor count — never triggers it, so
all existing pooling behaviour is preserved exactly. (The calibration backtest
exercises `joint_fit_likelihood`+`update` directly and does not touch this
path; the guard is `test_pooling.py`.)

---

## 4. HealthKit — split by role (FUTURE wiring)

HealthKit signals enter the model through the identity bridge
`healthkit_subject_map` (de-identified `subject_id` ↔ tracking `patient_id`;
migration `010`, resolver `engine/tracking/healthkit_identity.py`). Phase 0
ships **only** the bridge — no prediction wiring. When wired, HealthKit data
splits into two distinct roles that must not be conflated:

1. **Proxy observations** — HealthKit quantities that *are* (or stand in for) a
   tracked biomarker (e.g. resting heart rate, body mass, VO₂max). These enter
   as additional **likelihood** observations `y_i` on θ, subject to their own
   measurement-noise model — they update the posterior, they do **not** change
   the prior.
2. **Behavioural covariates** — signals that modulate *responsiveness* but are
   not the outcome (e.g. sleep, activity minutes, adherence proxies). These
   enter as **feature adapters** contributing to `η` (the prior), via §2 — with
   ridge-shrunk `β_j` and honest `var_j`.

Keeping these on opposite sides of Bayes' rule prevents a covariate from being
double-counted as evidence of the effect it predicts.

---

## 5. Gated-later extensions (not in this PR)

- **Cross-biomarker covariance over a shared η.** See §6 — a design stub ships
  in this PR (inert, off-by-default); the wiring is gated.
- **Dose-response.** Replace θ with an effective `θ_eff = θ · s(dose)` for a
  saturating dose function `s`. Requires dose-stratified data the cohort does
  not yet have — gated behind data volume. Designed and stubbed in §7.

---

## 6. Cross-biomarker covariance (gated)

**Status: DESIGN STUB — `engine/tracking/cross_biomarker.py`, off by default
(`CROSS_BIOMARKER_ENABLED = False`), not wired into any prediction.** The module
ships pure, unit-tested matrix helpers and this specification; it does not touch
the posterior.

### 6.1 The model

Today each biomarker `k` for a (patient, peptide) is fit with its **own
independent** scalar θ_k and a 1-D Normal–Normal update (§1). Biomarkers within
a peptide's *mechanism cluster* are not independent, though: GLP-1's body
weight, HbA1c, waist and HOMA-IR co-move because they are downstream of the same
incretin response. Model a cluster's latents jointly as a multivariate normal:

$$\theta = (\theta_{k_1},\dots,\theta_{k_K}) \sim \mathcal N(\mu_0,\ \Sigma),\qquad
\mu_0 = \eta\, e,\quad e = (\text{expected\_pct}_{k_1},\dots)$$

$$\Sigma = D\,R\,D,\qquad D = \operatorname{diag}(\sigma_{0,k_1},\dots,\sigma_{0,k_K}),$$

with `R` a symmetric, unit-diagonal, **PSD** correlation matrix — the empirical
correlation of the *standardised* per-marker responses `z_k = (θ_k − μ0_k)/σ0_k`
across the cohort. Because `D = diag(σ0_k)` already carries the shared-η
magnitude (§6.2), `R` is **not** η-partialled: a shared η shows up precisely as
a nonzero off-diagonal in `R` (sign `sign(e_j e_k)`, attenuated by the panel
term), and residual physiology adds to it.

### 6.2 A shared η already induces positive coupling

The Phase-0 responder index η (`responder_index.py`) is a single scalar
**shared by every biomarker** of a (patient, peptide), and it is itself
uncertain (`Var(η)`). Because each prior mean is a linear image of that one
shared, uncertain η, the biomarkers are **already coupled** before any full Σ:

$$\operatorname{Cov}(\theta_j,\theta_k) = \text{expected\_pct}_j\cdot\text{expected\_pct}_k\cdot\operatorname{Var}(\eta),$$

a **rank-1** term `Var(η)·e eᵀ` (`shared_eta_covariance`) whose sign is
`sign(expected_pct_j · expected_pct_k)` — same-direction markers positively
coupled, opposite-direction negatively, with no new parameters.

Crucially, **Phase 0's own per-marker variance is already the diagonal of that
rank-1 matrix.** The prior SD is `σ0_k = hypot(sd(η)·|e_k|, panel_rel_sd·|e_k|)`
(`genetics.derive_prior`), so

$$\sigma_{0,k}^2 = \operatorname{Var}(\eta)\,e_k^2 \;+\; \text{panel\_rel\_sd}^2\, e_k^2,$$

whose first summand is exactly the `k`-th diagonal entry of `Var(η)·e eᵀ`. Phase
0 keeps that shared-η term **only on the diagonal** and pins the off-diagonal
(the cross-marker correlation) to zero.

The gated extension therefore does **not** add a covariance on top of `σ0²` —
that would double-count the shared-η variance already inside `σ0²`. It replaces
the diagonal-only prior with a **single** joint covariance `Σ = D R D` reusing
the *same* per-marker SDs `D = diag(σ0_k)`, turning on the off-diagonal via a
residual correlation `R`. `R = I` recovers Phase 0 exactly
(`assemble_cluster_covariance` returns `diag(σ0_k²)`); a positive off-diagonal
restores the coupling a shared η already implies. The rank-1 `Var(η)·e eᵀ` is
the *justification* for the sign pattern of `R`'s off-diagonals, not a term
summed alongside `D R D`.

### 6.3 Joint posterior

With prior `θ ~ N(μ0, Σ)` and observation vector `ȳ` with covariance `Σ_obs`,
the conjugate update is the multivariate Normal–Normal step in precision form:

$$\Lambda_{\text{post}} = \Sigma^{-1} + \Sigma_{\text{obs}}^{-1},\qquad
\mu_{\text{post}} = \Lambda_{\text{post}}^{-1}\big(\Sigma^{-1}\mu_0 + \Sigma_{\text{obs}}^{-1}\bar y\big).$$

Off-diagonal entries of `Λ_post` are the channel by which a strong, well-measured
marker sharpens a coupled, sparsely-measured one. **If `Σ` and `Σ_obs` are both
diagonal (`R = I`) this decouples into `K` independent scalar updates
`τ_post = τ0 + τy` — byte-for-byte today's `bayes.update`.** That is the
inert-by-construction guarantee.

### 6.4 Why it's gated

- **Σ is unidentifiable without cohort volume.** A K×K correlation needs O(K²)
  residual pairs per cluster to estimate stably; the tracking cohort is far too
  small today. A plugged-in Σ would be mostly sampling noise.
- **It breaks the coverage contract.** Off-diagonal precision *narrows* credible
  intervals. Wrong correlations ⇒ overconfident intervals ⇒ the calibration
  backtest's coverage guarantee (the honesty contract for this subsystem)
  silently fails. Independent-per-marker is the conservative default that never
  claims cross-marker information it cannot back.

### 6.5 Intended integration point

`analysis.predict_response` currently loops one biomarker at a time. Un-gating
means: group a (patient, peptide)'s requested markers into their mechanism
cluster (`MECHANISM_CLUSTERS`), replace the per-marker `bayes.update` with a
single multivariate update (§6.3) over the cluster, then slice `μ_post`/`Λ_post`
back to the requested marker. That prediction-loop refactor is deliberately out
of scope for this stub.

---

## 7. Dose–response (gated)

**Status: design-only stub, feature-gated OFF.** Implemented in
`engine/tracking/dose_response.py` behind the module constant
`DOSE_RESPONSE_ENABLED = False`. Nothing in `predict_response` (or anywhere
else in `engine/`) imports it, so it is inert with respect to every live
prediction — the test suite, including the calibration backtest, is unaffected.
Unit tests for the maths live in
`tests/test_engine/test_tracking/test_dose_response.py`.

### 7.1 The model

θ (§1) is the fractional change from baseline *at plateau under a peptide's
reference dose*. Away from that reference, we scale θ by a saturating
Emax/EC50 response. With Hill coefficient fixed at 1, the raw response is

$$\text{emax}(d) = \frac{d}{d + \text{EC}_{50}}\qquad(\text{monotone}\uparrow,\ \to 1\text{ as }d\to\infty)$$

Because θ is *defined at the reference dose* `d_ref`, we normalise against it so
the multiplier is exactly 1 there:

$$s(d) = \frac{\text{emax}(d)}{\text{emax}(d_\text{ref})}
      = \frac{d/(d+\text{EC}_{50})}{d_\text{ref}/(d_\text{ref}+\text{EC}_{50})}$$

Properties (asserted in the unit tests):

- `s(d_ref) = 1` — the reference dose is the anchor.
- `s` is strictly increasing in `d`.
- `s` saturates at the finite plateau `s(∞) = 1 + EC₅₀/d_ref` (**> 1** — the raw
  Emax tops out at 1, but dividing by `emax(d_ref) < 1` lifts the normalised
  plateau above 1).

The dose-scaled latent effect is

$$\theta_\text{eff} = \theta \cdot \frac{s(d)}{s(d_\text{ref})} = \theta\cdot s(d),$$

where the `/ s(d_ref)` term is identically 1 by construction (kept explicit in
`effective_theta` to mirror the spec and make `θ_eff = θ` at the reference dose
self-evident). Per-peptide `(EC₅₀, d_ref)` are **placeholders** in
`PEPTIDE_PARAMS` — illustrative anchors, not calibrated values.

### 7.2 Intended wiring point

When enabled, `θ_eff` replaces θ exactly where the latent effect enters the
prior in `predict_response`: the prior mean `μ₀ = η · expected_pct` (§1–§2)
becomes `μ₀ = η · expected_pct · s(dose)`, applied **before** the conjugate
update. Nothing downstream of the prior changes — the likelihood, kinetics
`a(w)`, and posterior update are untouched.

### 7.3 Why it is gated

The current tracking cohort is effectively **single-dose per peptide**, so
`EC₅₀` is unidentifiable: with no dose variation there is no signal to separate
the dose curve from the baseline effect, and fitting `EC₅₀` against single-dose
data would fit noise. That would inflate confidence and **break the calibrated
95% coverage** the backtest guards. The gate stays OFF until dose-varied cohort
data exists to identify and validate `EC₅₀` per peptide.
