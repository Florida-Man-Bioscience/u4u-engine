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

- **Cross-biomarker covariance over a shared η.** Multiple biomarkers for one
  (patient, peptide) share the same responder index; modelling them jointly
  with a covariance over the shared η would let a strong signal in one marker
  inform another. Requires a multivariate prior and careful identifiability
  work — gated.
- **Dose-response.** Replace θ with an effective `θ_eff = θ · s(dose)` for a
  saturating dose function `s`. Requires dose-stratified data the cohort does
  not yet have — gated behind data volume.
