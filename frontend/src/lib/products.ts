/**
 * Public marketing product pages (apex). Marketing-only copy —
 * no deep technical detail, no clinical claims.
 */

import {
  COMPANY_ORIGIN,
  CYTOGATE_ORIGIN,
  DRUG_DESIGN_ORIGIN,
  NANODISK_ORIGIN,
  U4U_PRIVACY_ORIGIN,
} from "@/lib/site";

export type ProductSlug =
  | "u4u"
  | "cytogate"
  | "vector-nanodisk"
  | "neurocreatine"
  | "u4u-privacy"
  | "next-gen-drug-development"
  | "discovery-informatics";

export type ProductAccent = {
  /** Small label color */
  label: string;
  /** Soft wash behind hero media / chips */
  wash: string;
  /** Strong accent for CTAs / rules */
  solid: string;
};

export type ProductPage = {
  slug: ProductSlug;
  name: string;
  shortName: string;
  eyebrow: string;
  tagline: string;
  description: string;
  metaDescription: string;
  /** One-line homepage card body */
  cardBody: string;
  tag: string;
  accent: ProductAccent;
  heroImage?: { src: string; webp?: string; alt: string };
  /** Optional product-page gallery (bench shots, not stock biotech). */
  screenshots?: { src: string; webp?: string; alt: string; caption: string }[];
  audience: string;
  pillarsHeading?: string;
  screenshotsHeading?: string;
  pillars: { title: string; body: string }[];
  promises: string[];
  statusNote: string;
  disclaimer: string;
  /** Optional portfolio subdomain (canonical can stay on apex) */
  portfolioOrigin?: string;
  ctaPrimary: { label: string; href: string };
  ctaSecondary: { label: string; href: string };
};

const brandGreen = {
  label: "#1a6b4a",
  wash: "#e8f4ee",
  solid: "#1a6b4a",
} as const;

export const PRODUCTS: Record<ProductSlug, ProductPage> = {
  u4u: {
    slug: "u4u",
    name: "PeptOdyssey",
    shortName: "PeptOdyssey",
    eyebrow: "Flagship platform · Decision support",
    tagline: "Peptide options, matched to the genome.",
    description:
      "PeptOdyssey is Florida Man Bioscience’s shipping platform — engine, clinician-readable dossier, iOS research capture, and tracker. It turns a genetic file into a structured options set. A licensed clinician stays in the loop. The dossier is not a prescription.",
    metaDescription:
      "PeptOdyssey — Florida Man Bioscience’s genome-aware peptide platform. Engine, clinician-readable dossier, iOS capture, and tracker. Not a prescription. Not a medical device.",
    cardBody:
      "Shipping platform: genome → structured dossier → follow-up, with a licensed clinician in the loop. A dossier, not a prescription.",
    tag: "Platform",
    accent: brandGreen,
    audience:
      "Individuals exploring genome-informed peptide context, licensed clinicians, and partners building modern care workflows.",
    pillarsHeading: "A dossier a clinician can read.",
    pillars: [
      {
        title: "Genome-aware options",
        body: "Turn a genetic file into peptide-relevant context — structured so a licensed clinician can actually read it.",
      },
      {
        title: "Dossier, not a prescription",
        body: "Priorities, cautions, and open questions. Software does not prescribe. A clinician stays in the loop.",
      },
      {
        title: "A loop that learns",
        body: "Pair the first read with follow-up signals so the picture can refine — still under clinical judgment.",
      },
    ],
    promises: [
      "Clinician in the loop — dossier, not a prescription",
      "Live path into PeptOdyssey analysis and tracking",
      "Privacy toolkit lane when files should stay local",
    ],
    statusNote:
      "Shipping product surface for analysis, dossier, tracking, and iOS research capture.",
    disclaimer:
      "Research and decision-support software. Not a medical device. Not a prescription. Not intended to diagnose, treat, cure, or prevent disease. Does not replace clinical judgment or genetic counseling.",
    ctaPrimary: {
      label: "Open PeptOdyssey",
      href: "/peptodyssey",
    },
    ctaSecondary: {
      label: "Start a genome analysis",
      href: "/peptodyssey/analyze",
    },
  },

  cytogate: {
    slug: "cytogate",
    name: "CytoGate",
    shortName: "CytoGate",
    eyebrow: "Lab software · Flow cytometry",
    tagline: "See the matrix. Gate with intent.",
    description:
      "CytoGate is Florida Man Bioscience’s flow-cytometry product. CytoCrunch is the desktop bench — compensation and QC you can inspect, plus an optional Assistant that proposes gates and experiment-design checklists. You Apply. Auto-gate still works if the Assistant is off.",
    metaDescription:
      "CytoGate — flow cytometry desktop (CytoCrunch) from Florida Man Bioscience. Compensation, QC, auto-gate, and a propose-only Assistant. Research software. Not a medical device.",
    cardBody:
      "Compensation, QC, and gating for real FCS sessions — with an optional propose-only Assistant.",
    tag: "Lab software",
    accent: {
      label: "#0e5a8a",
      wash: "#e8f1f8",
      solid: "#0e5a8a",
    },
    heroImage: {
      src: "/assets/img/cytogate-bench.png",
      webp: "/assets/img/cytogate-bench.webp",
      alt: "CytoCrunch bench: FSC-A × SSC-A density plot, strategy tree, Time QC strip, and compensation inspector",
    },
    screenshots: [
      {
        src: "/assets/img/cytogate-bench.png",
        webp: "/assets/img/cytogate-bench.webp",
        alt: "CytoCrunch bench with synthetic FCS, gating tools, Time QC, and CompQC controls",
        caption:
          "The bench — synthetic FCS, FSC-A × SSC-A, strategy tree, Time QC, and compensation on one surface.",
      },
      {
        src: "/assets/img/cytogate-matrix.png",
        webp: "/assets/img/cytogate-matrix.webp",
        alt: "CytoGate graphic: compensation matrix with the line See the matrix. Gate with intent.",
        caption: "Compensation you can inspect — not a black box.",
      },
    ],
    audience:
      "Core facilities, immunology labs, and research teams whose panels outgrew brittle stacks.",
    pillarsHeading: "What the bench actually does.",
    screenshotsHeading: "The bench — synthetic FCS.",
    pillars: [
      {
        title: "Compensation you can inspect",
        body: "Matrix, spillover, and CompQC live on the inspector — nudge a coefficient and see the plot, instead of trusting a hidden unmix.",
      },
      {
        title: "QC before the argument",
        body: "Time QC, clean-events, auto-gate, and FMO are first-class. Argue about biology after the file has been through QC — not before.",
      },
      {
        title: "Propose, then Apply",
        body: "Optional Assistant suggests gates and a panel/FMO checklist from summaries. No raw FCS to a vendor. Nothing applies until you do.",
      },
    ],
    promises: [
      "Desktop bench (CytoCrunch) for FCS sessions",
      "Compensation, Time QC, auto-gate, FMO, and CompQC on the inspector",
      "Optional Assistant: propose-only — human Apply, Auto-gate still works offline",
      "Company-backed support path via hello@flmanbiosci.net",
    ],
    statusNote:
      "Desktop bench under active development. Research software — not a clinical release.",
    disclaimer:
      "Research and laboratory software. Not a medical device. Not intended to diagnose, treat, cure, or prevent disease.",
    portfolioOrigin: CYTOGATE_ORIGIN,
    ctaPrimary: { label: "Contact the team", href: "mailto:hello@flmanbiosci.net" },
    ctaSecondary: { label: "Back to company home", href: "/" },
  },

  "vector-nanodisk": {
    slug: "vector-nanodisk",
    name: "Vector nanodisk",
    shortName: "Nanodisk",
    eyebrow: "Delivery research · Optionality",
    tagline: "A research option — not a marketed therapeutic.",
    description:
      "Vector nanodisk (MSP) is a research-stage delivery concept for peptide and nucleic-acid payloads — the long-horizon Deliver leg of Detect → Design → Deliver. It is optionality on the books, not a product you can buy and not a drug we sell.",
    metaDescription:
      "Vector nanodisk — research-stage delivery optionality at Florida Man Bioscience. Not a marketed therapeutic. Not an approved product.",
    cardBody:
      "Research optionality for payload delivery — not a marketed therapeutic.",
    tag: "Delivery research",
    accent: {
      label: "#92550a",
      wash: "#faf0e4",
      solid: "#92550a",
    },
    audience:
      "Partners and collaborators who already understand this is research optionality, not a SKU.",
    pillarsHeading: "Research optionality — labeled as such.",
    pillars: [
      {
        title: "Not a product you buy",
        body: "This page describes a research program. Not a drug, not a device, not a clinic offering.",
      },
      {
        title: "Same platform, later leg",
        body: "Detect is software. Design is Stage A visualization. Deliver sits further out on the clock.",
      },
      {
        title: "No assignment on this page",
        body: "We do not preview owners, licensors, or university vehicles here. Scientific collaboration talk only.",
      },
    ],
    promises: [
      "Research-stage positioning only — no purchase path",
      "No therapeutic or efficacy claims",
      "Contact for scientific conversation, not a license pitch",
    ],
    statusNote: "Research optionality. Not a shipped or marketed therapeutic.",
    disclaimer:
      "Research program only. Not an approved drug, biologic, or clinical product. No outcome guarantees. Not intended to diagnose, treat, cure, or prevent disease.",
    portfolioOrigin: NANODISK_ORIGIN,
    ctaPrimary: {
      label: "Ask about delivery research",
      href: "mailto:hello@flmanbiosci.net?subject=Vector%20nanodisk",
    },
    ctaSecondary: { label: "Company home", href: "/" },
  },

  neurocreatine: {
    slug: "neurocreatine",
    name: "Neurocreatine",
    shortName: "Neurocreatine",
    eyebrow: "Parked · Early discovery",
    tagline: "An early CNS note — not a lead program.",
    description:
      "Neurocreatine is a parked, early discovery track for CNS-oriented peptide ideas. It is on the roster so the portfolio is complete. It is not a consumer product, not a supplement, and not what Florida Man Bioscience leads with.",
    metaDescription:
      "Neurocreatine — parked early CNS peptide discovery at Florida Man Bioscience. Not a lead program. Not a marketed product.",
    cardBody:
      "Parked early discovery — CNS peptide ideas, not a lead product.",
    tag: "Parked discovery",
    accent: {
      label: "#1e4d8c",
      wash: "#e9eef7",
      solid: "#1e4d8c",
    },
    audience:
      "Scientific collaborators who already know this track exists. Not a consumer audience.",
    pillarsHeading: "Why this page is quiet.",
    pillars: [
      {
        title: "Parked, not launched",
        body: "Early notes, not a campaign. We keep the page so the roster is honest.",
      },
      {
        title: "No lead, no claims",
        body: "Nothing here is a protocol, a pill, or a clinical offer.",
      },
      {
        title: "Earns the next experiment",
        body: "If it ever moves, it will earn the next measurement. It has not.",
      },
    ],
    promises: [
      "Explicit parked status — not a shipping product",
      "No consumer, supplement, or clinical claims",
      "Conversation only if you already know why you are asking",
    ],
    statusNote: "Parked early discovery. Do not treat this as a shipping product.",
    disclaimer:
      "Research and discovery only. Not a marketed supplement, drug, or medical device. Not intended to diagnose, treat, cure, or prevent disease.",
    ctaPrimary: {
      label: "Company home",
      href: "/",
    },
    ctaSecondary: {
      label: "See the shipping platform",
      href: "/products/u4u",
    },
  },

  "u4u-privacy": {
    slug: "u4u-privacy",
    name: "U4U Privacy",
    shortName: "u4u-privacy",
    eyebrow: "Genomics toolkit · Local-first",
    tagline: "Work the file on hardware you control.",
    description:
      "u4u-privacy is a local-first consumer genomics toolkit. Variant work and related utilities run on Windows, macOS, or Linux you own. The starting assumption is not “upload everything.”",
    metaDescription:
      "u4u-privacy — local-first consumer genomics toolkit from Florida Man Bioscience. Process genetic files on hardware you control. Not a diagnostic service.",
    cardBody:
      "Local-first genomics toolkit — process genetic files on hardware you control.",
    tag: "Privacy toolkit",
    accent: brandGreen,
    audience:
      "Privacy-conscious individuals, researchers, and builders who refuse “upload everything” defaults.",
    pillarsHeading: "Local-first, on purpose.",
    pillars: [
      {
        title: "Your machine first",
        body: "Pipelines are designed to run locally. Network is an opt-in (for example a public reference), not the default hop.",
      },
      {
        title: "Files you already have",
        body: "Consumer genotype exports and common genomic formats are in scope — without making a vendor the first stop.",
      },
      {
        title: "A different trust model",
        body: "PeptOdyssey is the clinic-facing dossier. This toolkit is for when the file should stay put.",
      },
    ],
    promises: [
      "Desktop installers: Windows / macOS / Linux",
      "Local-first posture — no upload-everything default",
      "Not a diagnostic service; not a substitute for genetic counseling",
    ],
    statusNote:
      "Desktop app: Windows / macOS / Linux installers via the product host and GitHub Releases.",
    disclaimer:
      "Consumer and research utilities. Not a medical device. Not a diagnostic service. Does not replace clinical genetic counseling.",
    portfolioOrigin: U4U_PRIVACY_ORIGIN,
    ctaPrimary: {
      label: "Buy / download Desktop",
      href: "https://u4u-privacy.flmanbiosci.net/#buy",
    },
    ctaSecondary: { label: "Explore PeptOdyssey", href: "/peptodyssey" },
  },

  "next-gen-drug-development": {
    slug: "next-gen-drug-development",
    name: "Next-gen drug design",
    shortName: "Drug design lab",
    eyebrow: "Design platform · Stage A",
    tagline: "See the structure. Design in software — not a wet lab.",
    description:
      "Next-gen drug design is Florida Man Bioscience’s Stage A surface: local structure visualization (desktop and VR) and a simulated design–build–test–learn loop for peptide and protein work. Software you can look at. Not a wet lab. Not a therapeutic.",
    metaDescription:
      "Next-gen drug design from Florida Man Bioscience — Stage A structure visualization for peptide and protein work. Software, not a wet lab. No therapeutic claims.",
    cardBody:
      "Stage A design and visualization for peptide and protein work — software, not a wet lab.",
    tag: "Design lab",
    accent: {
      label: "#5b3d8c",
      wash: "#f1ecf8",
      solid: "#5b3d8c",
    },
    audience:
      "Scientists and R&D leads who want a structure-guided design surface, not a robotics brochure.",
    pillarsHeading: "Stage A — design and visualization.",
    pillars: [
      {
        title: "See the structure",
        body: "Desktop and headset views of local structures so design talk stays on the molecule, not a slide deck.",
      },
      {
        title: "A simulated loop",
        body: "Design, evaluate, and record a cycle with simulated build/test economics. Lab robots are a later stage — not this one.",
      },
      {
        title: "Honest non-goals",
        body: "No wet-lab claim. No therapeutic claim in the UI. No Stage B hardware.",
      },
    ],
    promises: [
      "Stage A software: structure visualization and a simulated design loop",
      "Desktop and VR entry points",
      "Explicit non-goals: not a wet lab, not a drug",
    ],
    statusNote:
      "Stage A design surface under active development. Not a clinical or wet-lab product.",
    disclaimer:
      "Research and design software. Not a medical device. Not a substitute for regulated laboratory processes. No therapeutic claims.",
    portfolioOrigin: DRUG_DESIGN_ORIGIN,
    ctaPrimary: {
      label: "Request a design-lab conversation",
      href: "mailto:hello@flmanbiosci.net?subject=Next-gen%20drug%20development",
    },
    ctaSecondary: { label: "Company home", href: "/" },
  },

  "discovery-informatics": {
    slug: "discovery-informatics",
    name: "Discovery Informatics",
    shortName: "Discovery Informatics",
    eyebrow: "Research software · Wave 0",
    tagline:
      "A jailed science-agent OS: PI ask → routed evidence → versioned artifacts + METHODS + cannots.",
    description:
      "Discovery Informatics is Florida Man Bioscience’s science-agent operating system. A PI ask is routed, identifiers are normalized, the smallest public-API skill set runs, and the desk gets versioned artifacts plus METHODS and cannots. Wave 0 productization — not a shipping SaaS login.",
    metaDescription:
      "Discovery Informatics — a jailed science-agent OS from Florida Man Bioscience. PI ask to routed evidence, versioned artifacts, METHODS, and cannots. Wave 0 research software. Not a medical device.",
    cardBody:
      "Jailed science-agent OS: PI ask → routed evidence → artifacts + METHODS + cannots. Wave 0, unpriced.",
    tag: "Science-agent OS",
    accent: brandGreen,
    audience:
      "Lab PIs and informatics leads who want a jailed agent loop on their own desk — not a gene we found, not a grant writer.",
    pillarsHeading: "The loop, not a result.",
    pillars: [
      {
        title: "Ask → route → artifacts",
        body: "Normalize IDs, run the smallest skill set, write versioned files. Parallel only on independent lanes.",
      },
      {
        title: "METHODS and cannots",
        body: "Every run records methods and what the public APIs or corpus could not support. Missing is not false.",
      },
      {
        title: "Tenant jail",
        body: "Exclusive worktrees, localhost RAG sidecar, customer desk. The factory ships empty of anyone else’s trees.",
      },
    ],
    promises: [
      "Wave 0 productization — not a SaaS login",
      "Unpriced SKUs: DI-OS Core, DI-RAG Sidecar, DI-Jail, DI-ELN Logistics",
      "Related: Protein Chemistry is the structure/VR design surface",
    ],
    statusNote:
      "Wave 0 productization. Research software — not a shipping SaaS login.",
    disclaimer:
      "Research software. Not a medical device. Not grant submission. Not intended to diagnose, treat, cure, or prevent disease. Occupancy is not a requirement. Missing in a corpus is not a negative result. Strategy that commits the bench escalates to the PI.",
    ctaPrimary: {
      label: "Open a conversation",
      href: "mailto:hello@flmanbiosci.net?subject=Discovery%20Informatics",
    },
    ctaSecondary: {
      label: "Protein Chemistry",
      href: "/products/next-gen-drug-development",
    },
  },
};

export const PRODUCT_LIST: ProductPage[] = [
  PRODUCTS.u4u,
  PRODUCTS["next-gen-drug-development"],
  PRODUCTS["discovery-informatics"],
  PRODUCTS.cytogate,
  PRODUCTS["u4u-privacy"],
  PRODUCTS["vector-nanodisk"],
  PRODUCTS.neurocreatine,
];

export function productPath(slug: ProductSlug): string {
  return `/products/${slug}`;
}

export function productCanonical(slug: ProductSlug): string {
  return `${COMPANY_ORIGIN}${productPath(slug)}`;
}

export function isProductSlug(value: string): value is ProductSlug {
  return value in PRODUCTS;
}
