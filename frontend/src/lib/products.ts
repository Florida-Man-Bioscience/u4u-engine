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
  /** Short, plain-language case — why this program exists. */
  whyItMatters: string;
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
      "PeptOdyssey turns a genetic file into a structured set of peptide options a licensed clinician can review. It is research and decision-support software — not a prescription, not a diagnosis, and not a claim that any peptide will work. Evidence grades and citations travel with the dossier so unknowns stay visible.",
    whyItMatters:
      "People are using peptides faster than the facts. A DNA file is not a care plan. Ancestry companies hold genomes; peptide clinics ship vials; neither hands a clinician a graded options list. PeptOdyssey sits in that gap. Success is not that a peptide worked. Success is every statement having a grade, a clinician who can see why, and nobody confusing the dossier with a prescription.",
    metaDescription:
      "PeptOdyssey — genome-informed peptide options a licensed clinician can review. Research software, not a prescription, not a medical device.",
    cardBody:
      "Genome-informed peptide options for individuals and clinicians — research software, not a prescription.",
    tag: "Platform",
    accent: brandGreen,
    audience:
      "Individuals exploring genome-informed peptide context, licensed clinicians, and partners building modern care workflows.",
    pillarsHeading: "A dossier a clinician can read.",
    pillars: [
      {
        title: "Genome in, options out",
        body: "Upload or ingest a genetic file. Get a clinician-readable packet: context, flags, and options tied to published evidence — not a shopping cart.",
      },
      {
        title: "A licensed clinician stays in the loop",
        body: "The dossier is built to be reviewed by a human with a license. It does not replace clinical judgment or genetic counseling.",
      },
      {
        title: "Grades, not guarantees",
        body: "Approved drugs, compounding caveats, and unapproved compounds are not the same thing. Where human evidence is thin, the product says so.",
      },
    ],
    promises: [
      "Clinician in the loop — dossier, not a prescription",
      "Evidence grades and citations travel with the options",
      "Live path into analysis and tracking",
      "Privacy toolkit lane when files should stay local",
    ],
    statusNote:
      "Shipping platform (Detect). Design is Stage A. Delivery stays research. Not a claim of clinical proof.",
    disclaimer:
      "PeptOdyssey is research and decision-support software. It is not a medical device. It is not intended to diagnose, treat, cure, or prevent any disease. The dossier is not a prescription and does not replace clinical judgment or genetic counseling. A licensed clinician remains responsible for care. Florida Man Bioscience does not claim that peptide options listed in a dossier are safe or effective for any person.",
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
      "CytoGate is Florida Man Bioscience’s flow-cytometry product. CytoCrunch is the desktop bench: compensation and QC you can inspect, Time QC and clean-events, plus an optional Assistant that proposes gates and experiment-design checklists. A human Applies. Auto-gate still works if Assistant is off. Raw FCS stays on your machine.",
    whyItMatters:
      "The hard part of flow cytometry is no longer acquiring colors. It is not lying to yourself in software: dyes overlap, runs clog, and two labs can get different percentages from the same cells. CytoCrunch is a local bench that lets you see the compensation matrix, check run QC, and gate with intent.",
    metaDescription:
      "CytoGate — local flow-cytometry desktop (CytoCrunch). See the compensation matrix, check run QC, gate with intent. Research software. Not a medical device.",
    cardBody:
      "Local desktop cytometry for cores and immunology labs. See compensation. Keep the file. Gate on purpose.",
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
    pillarsHeading: "See the matrix. Gate with intent.",
    screenshotsHeading: "The bench — synthetic FCS.",
    pillars: [
      {
        title: "Inspect the matrix",
        body: "Compensation and unmix you can see — spillover and residual CompQC on the inspector, not a hidden black box.",
      },
      {
        title: "QC before phenotype",
        body: "Time QC, clean-events, FMO helpers. Argue about biology after the file has been through QC — not before.",
      },
      {
        title: "Propose, then Apply",
        body: "Optional Assistant suggests a gating tree and a panel checklist. You Apply or Reject. No silent writes. No raw FCS to a cloud model.",
      },
    ],
    promises: [
      "Desktop bench (CytoCrunch) for FCS sessions",
      "Compensation, Time QC, auto-gate, FMO, and CompQC on the inspector",
      "Optional Assistant: propose-only — human Apply, Auto-gate still works offline",
      "Company-backed support path via hello@flmanbiosci.net",
    ],
    statusNote:
      "Lab software in active build. Desktop CytoCrunch first. Research use. Assistant is optional and propose-only.",
    disclaimer:
      "CytoGate / CytoCrunch is research analysis software. It is not a medical device, is not intended to diagnose, treat, cure, or prevent any disease, and is not a clinical or IVD release. Automated or proposed gates do not replace experimental controls or a cytometrist’s judgment. No raw list-mode FCS is sent to a vendor in the default desktop configuration.",
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
      "Vector nanodisk (MSP) is a research-stage delivery concept for peptide and nucleic-acid payloads — the long-horizon Deliver leg of Detect → Design → Deliver. It is optionality on the books, not a SKU, not a marketed therapeutic, and not an approved product. Contact is a scientific conversation, not a license pitch.",
    whyItMatters:
      "Many of the most specific molecules we can design never become treatments because the body destroys them, dumps them in the liver, or locks them inside the cell. Delivery is the bottleneck. Vector nanodisk is a research option on that problem — not a medicine we sell.",
    metaDescription:
      "Vector nanodisk — research-stage delivery optionality at Florida Man Bioscience. Not a marketed therapeutic. Not for sale.",
    cardBody:
      "Research-stage delivery optionality for peptide and nucleic-acid payloads. Not a marketed therapeutic. Not for sale.",
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
        title: "The problem is delivery",
        body: "Peptides and nucleic acids fail on stability, targeting, immunogenicity, and getting out of the cell’s trash compartment. That bottleneck is documented. It is not an FMB efficacy story.",
      },
      {
        title: "A research platform, not a medicine",
        body: "If this work is funded, the questions are measurements: cargo protection, uptake versus known particles, simple immune and serum readouts. Null results are in scope.",
      },
      {
        title: "No purchase path",
        body: "There is no order form, no clinic offering, no dosing, no outcome guarantee. Institutional IP stays held out.",
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
      "Neurocreatine is a parked, early discovery track. It is on the roster so the portfolio is complete. It is not a consumer product, not a supplement, and not what Florida Man Bioscience leads with. If it ever moves, it will earn the next measurement. It has not.",
    whyItMatters:
      "This page exists so the roster is honest. It is not a launch, not a nootropic, and not a treatment offer. FMB has no animal or human Neurocreatine data to show.",
    metaDescription:
      "Neurocreatine — parked early CNS discovery at Florida Man Bioscience. Not a lead program. Not a marketed product. Not a supplement.",
    cardBody:
      "Parked early discovery — a CNS creatine question, not a lead product.",
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
      "U4U Privacy is a local-first toolkit for people who already have a consumer DNA file and do not want to upload it again. Variant work and utilities run on Windows, macOS, or Linux you own. The starting assumption is not upload-everything. Research and education software only.",
    whyItMatters:
      "If you already have a DNA file, almost every next product asks you to upload it. That is a custody choice, not a scientific one. U4U Privacy is the opposite offer: work the file on a computer you own. This software is not building another matching pool. It cannot make you invisible to relatives who upload elsewhere — and it does not pretend to.",
    metaDescription:
      "U4U Privacy — local-first consumer genomics toolkit. Work a DNA file on hardware you control. Not a diagnostic service. Not a medical device.",
    cardBody:
      "Local-first consumer genomics. Work a DNA file on hardware you control — not a clinic dossier (that is PeptOdyssey).",
    tag: "Privacy toolkit",
    accent: brandGreen,
    audience:
      "Privacy-conscious individuals, researchers, and builders who refuse “upload everything” defaults.",
    pillarsHeading: "Local-first, on purpose.",
    pillars: [
      {
        title: "Local-first, not local-washing",
        body: "Analysis is meant to run on the user’s machine. Fetching a public reference is an explicit opt-in, not a silent cloud round-trip.",
      },
      {
        title: "Bring the file you already have",
        body: "Consumer genotype exports and common genomic formats are first-class. You do not buy a new spit kit from FMB.",
      },
      {
        title: "Research language on purpose",
        body: "Reports are inspectable utilities, not diagnoses. PeptOdyssey is the clinic-facing packet. This toolkit is for when the file should stay put.",
      },
    ],
    promises: [
      "Desktop installers: Windows / macOS / Linux",
      "Local-first posture — no upload-everything default",
      "Not a diagnostic service; not a substitute for genetic counseling",
    ],
    statusNote:
      "Active development. Desktop installers for Windows, macOS, and Linux via the product host and GitHub Releases. Not a diagnostic service.",
    disclaimer:
      "Research and education utilities only. Not a medical device. Not a diagnostic service. Does not replace clinical genetic counseling or clinical genetic testing. This software does not make you anonymous. FMB does not claim HIPAA certification for U4U Privacy.",
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
      "Next-gen drug design is Florida Man Bioscience’s Stage A surface for structure-guided peptide and protein work. Load a structure on the desktop or in a VR prototype; run a simulated design–build–test–learn loop; keep the default install local. It is software you can look at — not a wet lab, not a therapeutic, not Stage B robotics.",
    whyItMatters:
      "A sequence on a screen does not show how a molecule sits in space. Seeing the structure — and costing a pretend design cycle before anyone orders synthesis — is how some bad peptides never get made. That is the whole case. This is software, not a wet lab.",
    metaDescription:
      "Next-gen drug design — Stage A structure visualization and a simulated design loop. Software, not a wet lab. No therapeutic claims.",
    cardBody:
      "Stage A. See the structure on desktop and in VR. Design in software before anyone orders synthesis. Not a wet lab. Not a drug.",
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
        body: "Desktop plus a VR prototype so depth is not stuck on a flat screen. Sequence is not shape.",
      },
      {
        title: "Design in software",
        body: "A simulated design–build–test–learn loop with a cost ledger. Build and Test are seams, not instruments.",
      },
      {
        title: "Local-first",
        body: "Default config has no PHI and does not require a cloud notebook. Not a wet lab. Not a drug.",
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
      "A PI ask is routed, identifiers are normalized, and the smallest public-API skill set runs on your desk. You get versioned artifacts plus METHODS and cannots — not a chat bubble that forgets what it could not find. Wave 0 productization; not a shipping SaaS login. Related: Protein Chemistry is the structure/VR design surface, a different product.",
    whyItMatters:
      "A fluent chat answer is not a methods section. Labs lose a week stitching three paragraphs that never say which database was queried or what could not be found. Discovery Informatics is a jailed loop on the desk: smallest tools, versioned files, and an explicit list of cannots. Missing is not a negative result. The OS is not the PI.",
    metaDescription:
      "Discovery Informatics — a jailed science-agent OS. PI ask to routed evidence, versioned artifacts, METHODS, and cannots. Wave 0 research software. Not a medical device. Not a grant writer.",
    cardBody:
      "Jailed science-agent OS for lab PIs: PI ask → routed evidence → artifacts + METHODS + cannots. Wave 0. Not a gene finder. Not a grant writer.",
    tag: "Science-agent OS",
    accent: brandGreen,
    audience:
      "Lab PIs and informatics leads who want a jailed agent loop on their own desk — not a gene we found, not a grant writer.",
    pillarsHeading: "The loop, not a result.",
    pillars: [
      {
        title: "Routed, not rambling",
        body: "Identifier normalization and the smallest public-API skill set — not every tool, not a fishing expedition.",
      },
      {
        title: "METHODS + cannots",
        body: "What ran is written down. What was missing is a cannot, not a negative result. Occupancy is not a requirement.",
      },
      {
        title: "Tenant jail",
        body: "Exclusive worktrees, localhost RAG sidecar, customer desk. Unpublished asks stay on the desk. Strategy that commits the bench escalates to the PI.",
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
      "Research software. Not a medical device. Not grant submission. Not intended to diagnose, treat, cure, or prevent disease. Occupancy is not a requirement. Missing in a corpus is not a negative result. Strategy that commits the bench escalates to the PI. Wave 0 — no customer counts or live SaaS claims.",
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
