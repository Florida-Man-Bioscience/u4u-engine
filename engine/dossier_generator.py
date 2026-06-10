"""
engine/dossier_generator.py
============================
Generates self-contained HTML dossier reports for each peptide therapy
recommendation, styled to match the PeptOdyssey dossier template.

Public interface
----------------
    generate_dossiers(pipeline_result: dict) -> dict[str, str]
        Returns a mapping of peptide_name -> HTML string.
"""

from __future__ import annotations
import html
import json
from datetime import datetime, timezone

_INVESTIGATIONAL_DISCLAIMER = (
    "This peptide is investigational and not FDA-approved for this use. A match "
    "between your genetics and this peptide's target pathways is a mechanistic "
    "observation only — it is NOT a prediction that the therapy will work for you."
)


# ─────────────────────────────────────────────────────────────────────────────
# CSS (extracted from dossier.html design system)
# ─────────────────────────────────────────────────────────────────────────────

_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
:root {
    --ink: #0d1117; --ink-2: #3a3f4a; --ink-3: #6b7280; --ink-4: #9ca3af;
    --surface: #ffffff; --surface-2: #f5f4f0; --surface-3: #edecea; --surface-4: #e3e1db;
    --accent: #1a6b4a; --accent-light: #e1f3eb; --accent-mid: #2d8f61; --accent-dark: #0f4530;
    --blue: #1e4d8c; --blue-light: #e8eef8; --blue-mid: #3d6499;
    --amber: #92550a; --amber-light: #fdf3e3;
    --red: #8b2020; --red-light: #fbeaea;
    --border: #dbd9d3; --border-light: #edecea;
    --radius: 6px; --radius-lg: 10px;
}
@media print {
    body { print-color-adjust: exact; -webkit-print-color-adjust: exact; background: white; }
    .no-print { display: none !important; }
    .page { margin: 0 auto !important; border: none !important; }
}
body { font-family: 'Outfit', sans-serif; font-size: 13px; line-height: 1.6; color: var(--ink); background: var(--surface-2); }
.page { width: 794px; margin: 32px auto; background: var(--surface); border: 1px solid var(--border); position: relative; overflow: hidden; }
.header { display: grid; grid-template-columns: 1fr auto; align-items: center; padding: 36px 40px 28px; background: var(--blue-mid); }
.brand-name { font-family: 'DM Serif Display', serif; font-size: 32px; letter-spacing: -0.5px; color: #fff; line-height: 1; }
.brand-tagline { font-size: 11px; letter-spacing: 0.12em; text-transform: uppercase; color: rgba(255,255,255,0.6); font-weight: 500; }
.meta-grid { display: grid; grid-template-columns: auto auto; gap: 4px 16px; }
.meta-label { font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase; color: rgba(255,255,255,0.5); font-weight: 500; text-align: right; }
.meta-value { font-family: 'DM Mono', monospace; color: #fff; font-size: 12px; }
.body { padding: 28px 40px 36px; display: flex; flex-direction: column; gap: 24px; }
.section-head { display: flex; align-items: center; gap: 12px; padding-bottom: 8px; border-bottom: 1.5px solid var(--ink); }
.section-num { font-family: 'DM Serif Display', serif; font-size: 26px; line-height: 1; color: var(--accent); }
.section-title { font-family: 'DM Serif Display', serif; font-size: 22px; line-height: 1.1; color: var(--ink); }
.section-sub { margin-left: auto; font-size: 10.5px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink-3); font-weight: 500; }
.panel-label { font-size: 9.5px; letter-spacing: 0.14em; text-transform: uppercase; font-weight: 700; color: var(--ink-3); margin-bottom: 8px; }
.info-card { border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 14px 16px; background: var(--surface); margin-bottom: 10px; }
.info-card.highlight { background: var(--accent-light); border-color: var(--accent); border-width: 1.5px; }
.info-card.warn { background: var(--amber-light); border-color: #d4890a; border-width: 1.5px; }
.variant-table { width: 100%; border-collapse: collapse; margin-top: 4px; }
.variant-table th, .variant-table td { text-align: left; padding: 5px 8px; font-size: 11.5px; border-bottom: 0.5px solid var(--border-light); }
.variant-table th { font-size: 9.5px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink-3); font-weight: 600; border-bottom: 1px solid var(--border); }
.variant-table td.gene { font-weight: 600; color: var(--ink); }
.variant-table td.mono { font-family: 'DM Mono', monospace; color: var(--ink-2); }
.db-tag { display: inline-block; font-size: 9px; padding: 1px 6px; border-radius: 8px; font-weight: 600; letter-spacing: 0.04em; margin-right: 3px; margin-bottom: 2px; }
.tag-clinvar { background: var(--red-light); color: var(--red); }
.tag-gnomad { background: var(--blue-light); color: var(--blue); }
.tag-uniprot { background: #e8f4e8; color: #2d6a2d; }
.tag-pharmgkb { background: #f0e8f4; color: #5d2d8c; }
.tag-gwas { background: var(--amber-light); color: var(--amber); }
.tier-badge { display: inline-block; font-size: 11px; padding: 3px 10px; border-radius: 12px; font-weight: 600; }
.tier-strong { background: var(--accent-light); color: var(--accent-dark); }
.tier-altered { background: var(--amber-light); color: var(--amber); }
.tier-caution { background: var(--red-light); color: var(--red); }
.tier-baseline { background: var(--surface-3); color: var(--ink-3); }
.detail-block { margin-top: 8px; padding: 10px 14px; background: var(--surface-2); border-left: 3px solid var(--accent); border-radius: 0 var(--radius) var(--radius) 0; font-size: 11.5px; color: var(--ink-2); line-height: 1.55; }
.detail-block strong { color: var(--ink); }
.footer { display: flex; align-items: center; justify-content: space-between; padding: 14px 40px; border-top: 1px solid var(--border); background: var(--surface-2); margin-top: auto; }
.footer-brand { font-family: 'DM Serif Display', serif; font-size: 14px; color: var(--ink-2); }
.footer-note { font-size: 9.5px; color: var(--ink-3); text-align: center; max-width: 440px; line-height: 1.4; }
.print-bar { width: 794px; margin: 0 auto 12px; display: flex; justify-content: flex-end; }
.btn { font-family: 'Outfit', sans-serif; font-size: 13px; font-weight: 500; padding: 8px 18px; border-radius: 6px; cursor: pointer; border: 1.5px solid var(--border); background: var(--surface); color: var(--ink-2); }
.btn:hover { background: var(--surface-3); }
.drug-item { padding: 6px 0; border-bottom: 0.5px solid var(--border-light); font-size: 12px; }
.drug-item:last-child { border-bottom: none; }
.drug-name { font-weight: 600; color: var(--ink); }
.drug-effect { color: var(--ink-2); }
.drug-evidence { font-size: 10px; color: var(--ink-3); font-style: italic; }
.trait-item { padding: 4px 0; font-size: 12px; color: var(--ink-2); }
.trait-name { font-weight: 500; color: var(--ink); }
.trait-pval { font-family: 'DM Mono', monospace; font-size: 10.5px; color: var(--ink-3); }
"""


def _e(text: str | None) -> str:
    """HTML-escape a string, returning empty string for None."""
    return html.escape(str(text)) if text else ""


def _tier_class(tier: str) -> str:
    """Map a predicted tier to a CSS class."""
    t = tier.lower() if tier else ""
    if "strong" in t:
        return "tier-strong"
    if "altered" in t or "reduced" in t:
        return "tier-altered"
    if "caution" in t:
        return "tier-caution"
    return "tier-baseline"


def _render_variant_row(v: dict, target_genes: set) -> str:
    """Render a single variant as a table row."""
    genes = v.get("genes", [])
    if isinstance(genes, str):
        genes = [genes]
    matched = [g for g in genes if g.upper() in {tg.upper() for tg in target_genes}]
    if not matched:
        return ""

    rsid = _e(v.get("rsid", "—"))
    gene_str = _e(", ".join(matched))
    consequence = _e(v.get("consequence", "—"))
    clinvar = _e(v.get("clinvar", "—"))
    genotype = _e(v.get("genotype", "—"))
    zygosity = _e(v.get("zygosity", "—"))
    gnomad = v.get("gnomad_af")
    gnomad_str = f"{gnomad:.4f}" if gnomad is not None else "—"

    # Database badges
    badges = []
    if v.get("clinvar"):
        badges.append('<span class="db-tag tag-clinvar">ClinVar</span>')
    if v.get("gnomad_af") is not None:
        badges.append('<span class="db-tag tag-gnomad">gnomAD</span>')
    if v.get("uniprot"):
        badges.append('<span class="db-tag tag-uniprot">UniProt</span>')
    if v.get("pharmgkb"):
        badges.append('<span class="db-tag tag-pharmgkb">PharmGKB</span>')
    if v.get("gwas"):
        badges.append('<span class="db-tag tag-gwas">GWAS</span>')

    return f"""<tr>
        <td class="gene">{gene_str}</td>
        <td class="mono">{rsid}</td>
        <td class="mono">{genotype}</td>
        <td>{zygosity}</td>
        <td>{consequence}</td>
        <td>{clinvar}</td>
        <td class="mono">{gnomad_str}</td>
        <td>{"".join(badges)}</td>
    </tr>"""


def _render_variant_details(v: dict, target_genes: set) -> str:
    """Render detailed database annotations for a variant."""
    genes = v.get("genes", [])
    if isinstance(genes, str):
        genes = [genes]
    matched = [g for g in genes if g.upper() in {tg.upper() for tg in target_genes}]
    if not matched:
        return ""

    blocks = []
    rsid = _e(v.get("rsid", "unknown"))

    # UniProt details
    uniprot = v.get("uniprot") or []
    for up in uniprot:
        if up.get("gene", "").upper() in {tg.upper() for tg in target_genes}:
            parts = [f"<strong>UniProt — {_e(up.get('gene', ''))}:</strong>"]
            if up.get("protein_name"):
                parts.append(f" {_e(up['protein_name'])}.")
            if up.get("function"):
                func = up["function"]
                if len(func) > 300:
                    func = func[:300] + "…"
                parts.append(f" {_e(func)}")
            if up.get("domains"):
                parts.append(f" Domains: {_e(', '.join(up['domains'][:5]))}.")
            blocks.append(f'<div class="detail-block">{"".join(parts)}</div>')

    # PharmGKB details
    pgkb = v.get("pharmgkb")
    if pgkb and pgkb.get("drug_interactions"):
        items_html = []
        for di in pgkb["drug_interactions"][:5]:
            drug = _e(di.get("drug", "Unknown"))
            effect = _e(di.get("effect", ""))
            evidence = _e(di.get("evidence_level", ""))
            items_html.append(
                f'<div class="drug-item">'
                f'<span class="drug-name">{drug}</span> '
                f'<span class="drug-effect">{effect}</span> '
                f'<span class="drug-evidence">{evidence}</span>'
                f'</div>'
            )
        blocks.append(
            f'<div class="detail-block"><strong>PharmGKB — {rsid}:</strong>'
            f'{"".join(items_html)}</div>'
        )

    # GWAS details
    gwas = v.get("gwas")
    if gwas and gwas.get("trait_associations"):
        items_html = []
        for ta in gwas["trait_associations"][:5]:
            trait = _e(ta.get("trait", ""))
            pval = ta.get("p_value")
            pval_str = f"{pval:.2e}" if pval is not None else "—"
            effect = _e(ta.get("effect_size", ""))
            items_html.append(
                f'<div class="trait-item">'
                f'<span class="trait-name">{trait}</span> '
                f'<span class="trait-pval">p={pval_str}</span> '
                f'{effect}'
                f'</div>'
            )
        blocks.append(
            f'<div class="detail-block"><strong>GWAS Catalog — {rsid}:</strong>'
            f'{"".join(items_html)}</div>'
        )

    return "\n".join(blocks)


def _render_peptide_dossier(rec: dict, variants: list[dict], now_str: str) -> str:
    """Render a complete HTML dossier for one peptide recommendation."""

    peptide_name = _e(rec.get("peptide_name", "Unknown"))
    category_display = _e(rec.get("category_display", ""))
    rationale = _e(rec.get("rationale", ""))
    predicted_tier = rec.get("predicted_tier", "Baseline")
    prediction_desc = _e(rec.get("prediction_description", ""))
    coverage = rec.get("coverage", 0)
    coverage_pct = f"{coverage * 100:.0f}%"
    target_genes = set(rec.get("genes_for_genotyping", []))
    genes_found = rec.get("genes_found", [])
    genes_missing = rec.get("genes_missing", [])

    # Filter variants relevant to this peptide's target genes
    relevant_variants = []
    for v in variants:
        v_genes = v.get("genes", [])
        if isinstance(v_genes, str):
            v_genes = [v_genes]
        if any(g.upper() in {tg.upper() for tg in target_genes} for g in v_genes):
            relevant_variants.append(v)

    # Variant table rows
    variant_rows = "\n".join(_render_variant_row(v, target_genes) for v in relevant_variants)
    if not variant_rows.strip():
        variant_rows = '<tr><td colspan="8" style="color:var(--ink-3);text-align:center;padding:16px;">No variants detected in target genes</td></tr>'

    # Variant detail blocks
    detail_blocks = "\n".join(_render_variant_details(v, target_genes) for v in relevant_variants)

    tier_css = _tier_class(predicted_tier)

    # ── Regulatory gating of the patient-facing efficacy claim ───────────────
    # For investigational (non-FDA-approved) peptides we must NOT present a
    # genetic "Predicted Efficacy" as if it forecasts clinical benefit. Show a
    # neutral, non-predictive pathway observation plus a prominent disclaimer.
    investigational = bool(rec.get("investigational"))
    if investigational:
        section1_title = "Genetic Pathway Analysis"
        section1_sub = "Investigational &middot; efficacy not established"
        pred_card_label = "Genetic Pathway Match (not a prediction of benefit)"
        pred_badge_text = _e(rec.get("pathway_match_label") or predicted_tier)
        pred_badge_css = "tier-baseline"
        disclaimer_html = (
            f'<div class="info-card warn" style="margin-top:10px;">'
            f'<div class="panel-label">Important — Investigational Therapy</div>'
            f'<div style="font-size:12px;color:var(--ink-2);line-height:1.5;">'
            f'{_e(rec.get("efficacy_disclaimer") or _INVESTIGATIONAL_DISCLAIMER)}'
            f'</div></div>'
        )
    else:
        section1_title = "Predicted Efficacy"
        section1_sub = category_display
        pred_card_label = "Prediction"
        pred_badge_text = _e(predicted_tier)
        pred_badge_css = tier_css
        disclaimer_html = ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>PeptOdyssey — {peptide_name} Dossier</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@400;500&family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
<style>{_CSS}</style>
</head>
<body>

<div class="print-bar no-print">
  <button class="btn" onclick="window.print()">Print / Save PDF</button>
</div>

<div class="page">

  <!-- HEADER -->
  <div class="header">
    <div>
      <div class="brand-name">PeptOdyssey</div>
      <div class="brand-tagline">Genetic Analysis Dossier &middot; {peptide_name}</div>
    </div>
    <div class="meta-grid">
      <span class="meta-label">Peptide</span>
      <span class="meta-value">{peptide_name}</span>
      <span class="meta-label">Category</span>
      <span class="meta-value">{category_display}</span>
      <span class="meta-label">Generated</span>
      <span class="meta-value">{now_str}</span>
    </div>
  </div>

  <!-- BODY -->
  <div class="body">

    <!-- §1 PREDICTION -->
    <section>
      <div class="section-head">
        <span class="section-num">1</span>
        <h2 class="section-title">{section1_title}</h2>
        <span class="section-sub">{section1_sub}</span>
      </div>

      <div class="info-card highlight" style="margin-top:14px;">
        <div class="panel-label">{pred_card_label}</div>
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
          <span class="tier-badge {pred_badge_css}">{pred_badge_text}</span>
          <span style="font-size:12px;color:var(--ink-2);">Coverage: <strong>{coverage_pct}</strong></span>
        </div>
        <div style="font-size:12px;color:var(--ink-2);line-height:1.5;">{prediction_desc}</div>
      </div>
      {disclaimer_html}

      <div class="info-card">
        <div class="panel-label">Rationale</div>
        <div style="font-size:12px;color:var(--ink-2);line-height:1.5;">{rationale}</div>
      </div>

      <div class="info-card">
        <div class="panel-label">Target Genes</div>
        <div style="font-size:12px;">
          <strong>Found:</strong> <span style="color:var(--accent);">{_e(", ".join(genes_found)) if genes_found else "None"}</span>
          &nbsp;&middot;&nbsp;
          <strong>Missing:</strong> <span style="color:var(--ink-3);">{_e(", ".join(genes_missing)) if genes_missing else "None"}</span>
        </div>
      </div>
    </section>

    <!-- §2 GENETIC EVIDENCE -->
    <section>
      <div class="section-head">
        <span class="section-num">2</span>
        <h2 class="section-title">Genetic Evidence</h2>
        <span class="section-sub">{len(relevant_variants)} variant(s) in target genes</span>
      </div>

      <div style="margin-top:14px;">
        <table class="variant-table">
          <thead>
            <tr>
              <th>Gene</th>
              <th>rsID</th>
              <th>Genotype</th>
              <th>Zygosity</th>
              <th>Consequence</th>
              <th>ClinVar</th>
              <th>gnomAD AF</th>
              <th>Sources</th>
            </tr>
          </thead>
          <tbody>
            {variant_rows}
          </tbody>
        </table>
      </div>
    </section>

    <!-- §3 DATABASE ANNOTATIONS -->
    <section>
      <div class="section-head">
        <span class="section-num">3</span>
        <h2 class="section-title">Database Annotations</h2>
        <span class="section-sub">UniProt &middot; PharmGKB &middot; GWAS Catalog</span>
      </div>

      <div style="margin-top:14px;">
        {detail_blocks if detail_blocks.strip() else '<div class="detail-block">No additional database annotations available for the detected variants.</div>'}
      </div>
    </section>

  </div><!-- /.body -->

  <!-- FOOTER -->
  <div class="footer">
    <div class="footer-brand">PeptOdyssey</div>
    <div class="footer-note">For clinician-supervised use. Recommendations are decision support, not a prescription. Database annotations are sourced from ClinVar, gnomAD, UniProt, PharmGKB, and the GWAS Catalog.</div>
  </div>

</div><!-- /.page -->

</body>
</html>"""


def generate_dossiers(pipeline_result: dict) -> dict[str, str]:
    """
    Generate HTML dossier reports for each peptide therapy recommendation.

    Parameters
    ----------
    pipeline_result : dict
        The full result dict returned by run_pipeline().

    Returns
    -------
    dict[str, str]
        Mapping of peptide_name -> self-contained HTML string.
    """
    recs = (pipeline_result.get("peptide_recommendations") or {}).get("recommendations", [])
    variants = pipeline_result.get("variants", [])

    now_str = datetime.now(timezone.utc).strftime("%d-%b-%Y").upper()

    dossiers = {}
    for rec in recs:
        name = rec.get("peptide_name", "Unknown")
        dossiers[name] = _render_peptide_dossier(rec, variants, now_str)

    return dossiers
