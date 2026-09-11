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
      "PeptOdyssey turns a genetic file into a structured set of peptide options a licensed clinician can review. Evidence grades and citations travel with the dossier so unknowns stay visible.",
    whyItMatters:
      "People are using peptides faster than the facts. Ancestry companies hold genomes; peptide clinics ship vials. PeptOdyssey writes the graded options list a licensed clinician can review. Success is every statement having a grade, and a clinician who can see why.",
    metaDescription:
      "PeptOdyssey — genome-informed peptide options a licensed clinician can review.",
    cardBody:
      "Genome-informed peptide options for individuals and clinicians.",
    tag: "Platform",
    accent: brandGreen,
    audience:
      "Individuals exploring genome-informed peptide context, licensed clinicians, and partners building modern care workflows.",
    pillarsHeading: "A dossier a clinician can read.",
    pillars: [
      {
        title: "Genome in, options out",
        body: "Upload or ingest a genetic file. Get a clinician-readable packet: context, flags, and options tied to published evidence.",
      },
      {
        title: "A licensed clinician stays in the loop",
        body: "The dossier is built to be reviewed by a human with a license.",
      },
      {
        title: "Evidence grades",
        body: "Approved drugs, compounding caveats, and unapproved compounds are labeled. Where human evidence is thin, the product says so.",
      },
    ],
    promises: [
      "A licensed clinician reviews the dossier",
      "Evidence grades and citations travel with the options",
      "Live path into analysis and tracking",
      "Privacy toolkit lane when files should stay local",
    ],
    statusNote:
      "Shipping platform (Detect). Design is Stage A. Delivery stays research.",
    disclaimer:
      "PeptOdyssey is research and decision-support software. A licensed clinician remains responsible for care.",
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
      "The hard part of flow cytometry is reading the file with intent: dyes overlap, runs clog, and labs need to see the same cells the same way. CytoCrunch is a local bench that lets you see the compensation matrix, check run QC, and gate with intent.",
    metaDescription:
      "CytoGate — local flow-cytometry desktop (CytoCrunch). See the compensation matrix, check run QC, gate with intent.",
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
        caption: "Compensation you can inspect.",
      },
    ],
    audience:
      "Core facilities, immunology labs, and research teams whose panels outgrew brittle stacks.",
    pillarsHeading: "See the matrix. Gate with intent.",
    screenshotsHeading: "The bench — synthetic FCS.",
    pillars: [
      {
        title: "Inspect the matrix",
        body: "Compensation and unmix you can see — spillover and residual CompQC on the inspector.",
      },
      {
        title: "QC before phenotype",
        body: "Time QC, clean-events, FMO helpers. Argue about biology after the file has been through QC.",
      },
      {
        title: "Propose, then Apply",
        body: "Optional Assistant suggests a gating tree and a panel checklist. You Apply or Reject. Raw FCS stays on your machine.",
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
      "CytoGate / CytoCrunch is research analysis software. A cytometrist Applies gates. Raw FCS stays on your machine.",
    portfolioOrigin: CYTOGATE_ORIGIN,
    ctaPrimary: { label: "Contact the team", href: "mailto:hello@flmanbiosci.net" },
    ctaSecondary: { label: "Back to company home", href: "/" },
  },

  "vector-nanodisk": {
    slug: "vector-nanodisk",
    name: "Vector nanodisk",
    shortName: "Nanodisk",
    eyebrow: "Delivery research · Optionality",
    tagline: "A research option for payload delivery.",
    description:
      "Vector nanodisk (MSP) is a research-stage delivery concept for peptide and nucleic-acid payloads — the long-horizon Deliver leg of Detect → Design → Deliver. Contact is a scientific conversation.",
    whyItMatters:
      "Many of the most specific molecules we can design fail on the way in: the body destroys them, dumps them in the liver, or locks them inside the cell. Delivery is the bottleneck. Vector nanodisk is a research option on that problem.",
    metaDescription:
      "Vector nanodisk — research-stage delivery optionality at Florida Man Bioscience.",
    cardBody:
      "Research-stage delivery optionality for peptide and nucleic-acid payloads.",
    tag: "Delivery research",
    accent: {
      label: "#92550a",
      wash: "#faf0e4",
      solid: "#92550a",
    },
    audience:
      "Partners and collaborators in delivery research.",
    pillarsHeading: "Research optionality.",
    pillars: [
      {
        title: "The problem is delivery",
        body: "Peptides and nucleic acids fail on stability, targeting, immunogenicity, and getting out of the cell’s trash compartment. That bottleneck is documented.",
      },
      {
        title: "A research platform",
        body: "If this work is funded, the questions are measurements: cargo protection, uptake versus known particles, simple immune and serum readouts. Null results are in scope.",
      },
      {
        title: "Scientific contact",
        body: "Talk with the team about the research program. Institutional IP stays held out.",
      },
    ],
    promises: [
      "Research-stage delivery program",
      "Scientific conversation with the team",
      "Institutional IP stays held out",
    ],
    statusNote: "Research optionality.",
    disclaimer:
      "Research program. Contact is a scientific conversation.",
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
    tagline: "An early CNS note.",
    description:
      "Neurocreatine is a parked, early discovery track. It is on the roster so the portfolio is complete. If it ever moves, it will earn the next measurement.",
    whyItMatters:
      "This page exists so the roster is complete and honest.",
    metaDescription:
      "Neurocreatine — parked early CNS discovery at Florida Man Bioscience.",
    cardBody:
      "Parked early discovery — a CNS creatine question.",
    tag: "Parked discovery",
    accent: {
      label: "#1e4d8c",
      wash: "#e9eef7",
      solid: "#1e4d8c",
    },
    audience:
      "Scientific collaborators who already know this track exists.",
    pillarsHeading: "Why this page is quiet.",
    pillars: [
      {
        title: "Parked, early notes",
        body: "Early notes. We keep the page so the roster is complete.",
      },
      {
        title: "Quiet on purpose",
        body: "This page is a roster entry.",
      },
      {
        title: "Earns the next experiment",
        body: "If it ever moves, it will earn the next measurement.",
      },
    ],
    promises: [
      "Parked early discovery",
      "Roster entry so the portfolio is complete",
      "Conversation if you already know why you are asking",
    ],
    statusNote: "Parked early discovery.",
    disclaimer:
      "Research and discovery. Parked early track.",
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
      "U4U Privacy is a local-first toolkit for people who already have a consumer DNA file. Variant work and utilities run on Windows, macOS, or Linux you own. Research and education software.",
    whyItMatters:
      "If you already have a DNA file, U4U Privacy lets you work it on a computer you own.",
    metaDescription:
      "U4U Privacy — local-first consumer genomics toolkit. Work a DNA file on hardware you control.",
    cardBody:
      "Local-first consumer genomics. Work a DNA file on hardware you control.",
    tag: "Privacy toolkit",
    accent: brandGreen,
    audience:
      "Privacy-conscious individuals, researchers, and builders who want files to stay local.",
    pillarsHeading: "Local-first, on purpose.",
    pillars: [
      {
        title: "Local-first",
        body: "Analysis runs on the user’s machine. Fetching a public reference is an explicit opt-in.",
      },
      {
        title: "Bring the file you already have",
        body: "Consumer genotype exports and common genomic formats are first-class.",
      },
      {
        title: "Research language on purpose",
        body: "Reports are inspectable utilities. PeptOdyssey is the clinic-facing packet. This toolkit is for when the file stays put.",
      },
    ],
    promises: [
      "Desktop installers: Windows / macOS / Linux",
      "Local-first analysis on hardware you control",
      "PeptOdyssey remains the clinic-facing dossier",
    ],
    statusNote:
      "Active development. Desktop installers for Windows, macOS, and Linux via the product host and GitHub Releases.",
    disclaimer:
      "Research and education utilities. Analysis runs on hardware you control.",
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
    tagline: "See the structure. Design in software.",
    description:
      "Next-gen drug design is Florida Man Bioscience’s Stage A surface for structure-guided peptide and protein work. Load a structure on the desktop or in a VR prototype; run a simulated design–build–test–learn loop; keep the default install local. Software you can look at.",
    whyItMatters:
      "Seeing the structure — and costing a pretend design cycle before anyone orders synthesis — is how some designs earn the next experiment. This is software you can look at.",
    metaDescription:
      "Next-gen drug design — Stage A structure visualization and a simulated design loop.",
    cardBody:
      "Stage A. See the structure on desktop and in VR. Design in software before anyone orders synthesis.",
    tag: "Design lab",
    accent: {
      label: "#5b3d8c",
      wash: "#f1ecf8",
      solid: "#5b3d8c",
    },
    audience:
      "Scientists and R&D leads who want a structure-guided design surface.",
    pillarsHeading: "Stage A — design and visualization.",
    pillars: [
      {
        title: "See the structure",
        body: "Desktop plus a VR prototype so depth lives in three dimensions.",
      },
      {
        title: "Design in software",
        body: "A simulated design–build–test–learn loop with a cost ledger. Build and Test are seams.",
      },
      {
        title: "Local-first",
        body: "Default config stays on your machine.",
      },
    ],
    promises: [
      "Stage A software: structure visualization and a simulated design loop",
      "Desktop and VR entry points",
      "Local-first default install",
    ],
    statusNote:
      "Stage A design surface under active development.",
    disclaimer:
      "Research and design software.",
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
      "A PI ask is routed, identifiers are normalized, and the smallest public-API skill set runs on your desk. You get versioned artifacts plus METHODS and cannots. Wave 0 productization. Related: Protein Chemistry is the structure/VR design surface.",
    whyItMatters:
      "Labs lose a week stitching three paragraphs. Discovery Informatics is a jailed loop on the desk: smallest tools, versioned files, and an explicit list of cannots. The PI decides.",
    metaDescription:
      "Discovery Informatics — a jailed science-agent OS. PI ask to routed evidence, versioned artifacts, METHODS, and cannots. Wave 0 research software.",
    cardBody:
      "Jailed science-agent OS for lab PIs: PI ask → routed evidence → artifacts + METHODS + cannots. Wave 0.",
    tag: "Science-agent OS",
    accent: brandGreen,
    audience:
      "Lab PIs and informatics leads who want a jailed agent loop on their own desk.",
    pillarsHeading: "The loop.",
    pillars: [
      {
        title: "Routed",
        body: "Identifier normalization and the smallest public-API skill set.",
      },
      {
        title: "METHODS + cannots",
        body: "What ran is written down. What was missing is a cannot. The PI decides occupancy.",
      },
      {
        title: "Tenant jail",
        body: "Exclusive worktrees, localhost RAG sidecar, customer desk. Unpublished asks stay on the desk. Strategy that commits the bench escalates to the PI.",
      },
    ],
    promises: [
      "Wave 0 productization",
      "Unpriced SKUs: DI-OS Core, DI-RAG Sidecar, DI-Jail, DI-ELN Logistics",
      "Related: Protein Chemistry is the structure/VR design surface",
    ],
    statusNote:
      "Wave 0 productization. Research software.",
    disclaimer:
      "Research software. Strategy that commits the bench escalates to the PI.",
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
