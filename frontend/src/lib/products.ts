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
  | "next-gen-drug-development";

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
  audience: string;
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
    tagline: "Peptide medicine, matched to the genome.",
    description:
      "PeptOdyssey is Florida Man Bioscience’s genome-aware peptide platform — engine, clinician-readable dossier, iOS research capture, and longitudinal tracker in one product. It turns genetic context into a clearer options set for licensed clinicians and the people they care for.",
    metaDescription:
      "PeptOdyssey — Florida Man Bioscience’s genome-aware peptide platform. Engine, dossier, iOS capture, and tracker. Not a medical device.",
    cardBody:
      "The shipping platform: genome → structured dossier → biomarker follow-up, with a licensed clinician in the loop.",
    tag: "Platform",
    accent: brandGreen,
    audience:
      "Individuals exploring genome-informed peptide context, licensed clinicians, and partners building modern care workflows.",
    pillars: [
      {
        title: "Genome-aware options",
        body: "Turn raw genetics into a clearer picture of peptide-relevant biology — structured for a licensed clinician to read.",
      },
      {
        title: "Personal, not generic",
        body: "Built around your file and your context, not a one-size handout. The goal is a decision-ready options set.",
      },
      {
        title: "A loop that learns",
        body: "Pair the first read with follow-up signals over time so the picture can refine as real-world data arrives.",
      },
    ],
    promises: [
      "Premium, fast-loading product marketing — message over chrome",
      "Live path into PeptOdyssey analysis and tracking",
      "Privacy toolkit lane when files should stay local",
    ],
    statusNote:
      "Shipping product surface for analysis, dossier, tracking, and iOS research capture.",
    disclaimer:
      "Research and decision-support software. Not a medical device. Not intended to diagnose, treat, cure, or prevent disease. Does not replace clinical judgment or genetic counseling.",
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
    eyebrow: "Lab software · Portfolio",
    tagline: "See your flow data with clarity.",
    description:
      "CytoGate is Florida Man Bioscience’s flow-analysis product surface — built for scientists who need trustworthy views of complex cell data, without wrestling brittle desktop stacks.",
    metaDescription:
      "CytoGate — flow cytometry analysis software from Florida Man Bioscience. Clear gating and strategy tools for real lab workflows.",
    cardBody:
      "Flow analysis software for modern labs — clearer views of complex cell data, built for real workflows.",
    tag: "Lab software",
    accent: {
      label: "#0e5a8a",
      wash: "#e8f1f8",
      solid: "#0e5a8a",
    },
    audience: "Core facilities, immunology labs, and research teams that live in FCS files.",
    pillars: [
      {
        title: "Built for real sessions",
        body: "Designed around the pace of experimental work — not demos that fall apart when files get large or panels get dense.",
      },
      {
        title: "Clarity over clutter",
        body: "A calmer interface for strategy and review so your team spends time on biology, not fighting the tool.",
      },
      {
        title: "Part of the FMB family",
        body: "A dedicated product surface under Florida Man Bioscience — with room to grow into releases, docs, and training.",
      },
    ],
    promises: [
      "Product-focused experience for flow analysis",
      "Portfolio host reserved for CytoGate releases",
      "Company-backed support path via hello@flmanbiosci.net",
    ],
    statusNote: "Product surface under active development.",
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
    eyebrow: "Delivery research · Program",
    tagline: "A research path for getting molecules where they need to go.",
    description:
      "Our vector nanodisk program explores a next-generation delivery vehicle for peptide and nucleic-acid payloads — the long-horizon “Deliver” leg of the Florida Man Bioscience platform.",
    metaDescription:
      "Vector nanodisk delivery research at Florida Man Bioscience — research-stage molecule delivery for peptide and nucleic-acid programs. Not a marketed therapeutic.",
    cardBody:
      "Research-stage delivery science — a long-horizon path for peptide and nucleic-acid payloads.",
    tag: "Delivery research",
    accent: {
      label: "#92550a",
      wash: "#faf0e4",
      solid: "#92550a",
    },
    heroImage: {
      src: "/assets/img/nanodisk.jpg",
      webp: "/assets/img/nanodisk.webp",
      alt: "Illustration of a nanodisk delivery concept",
    },
    audience: "Partners, investors, and collaborators evaluating FMB’s delivery research optionality.",
    pillars: [
      {
        title: "Delivery as a system",
        body: "We treat delivery as part of the same loop as matching and measurement — not a disconnected side project.",
      },
      {
        title: "Patient-relevant ambition",
        body: "Many promising molecules fail less on design than on access. This program studies how to carry payloads more carefully across barriers.",
      },
      {
        title: "Research first",
        body: "This is a scientific program with public notes and a reserved product host — not a marketed drug or clinical offering.",
      },
    ],
    promises: [
      "Transparent research-stage positioning",
      "Aligned with Detect → Design → Deliver",
      "Separable IP and program documentation as work matures",
    ],
    statusNote: "Research-stage molecule layer. Not a shipped therapeutic.",
    disclaimer:
      "Research program only. Not an approved drug, biologic, or clinical product. No outcome guarantees. Not intended to diagnose, treat, cure, or prevent disease.",
    portfolioOrigin: NANODISK_ORIGIN,
    ctaPrimary: { label: "Partner on delivery research", href: "mailto:hello@flmanbiosci.net?subject=Vector%20nanodisk" },
    ctaSecondary: { label: "Company home", href: "/" },
  },

  neurocreatine: {
    slug: "neurocreatine",
    name: "Neurocreatine",
    shortName: "Neurocreatine",
    eyebrow: "Discovery · CNS program",
    tagline: "Exploring peptides aimed at the mind and nervous system.",
    description:
      "Neurocreatine is an early discovery track exploring CNS-oriented peptide concepts — using Florida Man Bioscience’s analytics posture to triage ideas and keep go/no-go decisions grounded in measurable signals.",
    metaDescription:
      "Neurocreatine — early-stage CNS peptide discovery from Florida Man Bioscience. Research program; not a marketed product.",
    cardBody:
      "Early-stage CNS discovery — peptide concepts guided by measurement and careful triage.",
    tag: "Discovery",
    accent: {
      label: "#1e4d8c",
      wash: "#e9eef7",
      solid: "#1e4d8c",
    },
    heroImage: {
      src: "/assets/img/neurocreatine.jpg",
      webp: "/assets/img/neurocreatine.webp",
      alt: "Molecular illustration of a brain peptide concept",
    },
    audience: "Scientific collaborators and partners interested in CNS peptide discovery.",
    pillars: [
      {
        title: "Discovery with discipline",
        body: "We prioritize clear decision points over hype — candidates earn the next experiment.",
      },
      {
        title: "Measurement-minded",
        body: "Ideas are framed around signals you can track, so learning compounds as the program matures.",
      },
      {
        title: "Tied to the platform",
        body: "Neurocreatine sits inside the same FMB philosophy as our software loop: detect carefully, design deliberately, deliver only when ready.",
      },
    ],
    promises: [
      "Early-stage discovery framing (no product claims)",
      "Aligned with genome-aware and biomarker thinking",
      "Open to thoughtful scientific collaboration",
    ],
    statusNote: "Early discovery track. Not a consumer or clinical product.",
    disclaimer:
      "Research and discovery only. Not a marketed supplement, drug, or medical device. Not intended to diagnose, treat, cure, or prevent disease.",
    ctaPrimary: {
      label: "Discuss discovery collaboration",
      href: "mailto:hello@flmanbiosci.net?subject=Neurocreatine",
    },
    ctaSecondary: { label: "Company home", href: "/" },
  },

  "u4u-privacy": {
    slug: "u4u-privacy",
    name: "U4U Privacy",
    shortName: "u4u-privacy",
    eyebrow: "Genomics toolkit · Portfolio",
    tagline: "Your genome stays where you put it.",
    description:
      "u4u-privacy is a local-first consumer genomics toolkit — utilities for working with genetic files on hardware you control, with a privacy-first posture by design.",
    metaDescription:
      "u4u-privacy — local-first consumer genomics toolkit from Florida Man Bioscience. Privacy-first utilities for genetic files you control.",
    cardBody:
      "Local-first consumer genomics — tools that keep raw genetic data under your control.",
    tag: "Privacy toolkit",
    accent: brandGreen,
    audience: "Privacy-conscious individuals, researchers, and builders who refuse “upload everything” defaults.",
    pillars: [
      {
        title: "Local-first by default",
        body: "Process and explore on machines you trust. We design so sensitive files do not need a third-party cloud as the starting assumption.",
      },
      {
        title: "Clear boundaries",
        body: "Straightforward product language about what leaves your device — and what never has to.",
      },
      {
        title: "Kin to PeptOdyssey",
        body: "Part of the Florida Man Bioscience family: genome-aware products with different surfaces for different trust models.",
      },
    ],
    promises: [
      "Privacy-first product posture",
      "Dedicated portfolio host for the toolkit",
      "Company contact for partnership and feedback",
    ],
    statusNote: "Desktop app: Windows / macOS / Linux installers via product page + GitHub Releases.",
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
    eyebrow: "Design platform · Lab",
    tagline: "Design the molecule with your eyes open.",
    description:
      "Our next-generation drug design lab is a structure-guided visualization platform for peptide and protein work — immersive views and disciplined design loops. Software-first Stage A — not a wet-lab or clinical product.",
    metaDescription:
      "Next-gen drug design from Florida Man Bioscience — structure-guided visualization for peptide and protein programs. Stage A software; no therapeutic claims.",
    cardBody:
      "Structure-guided design lab — immersive visualization and disciplined loops for peptide and protein work.",
    tag: "Design lab",
    accent: {
      label: "#5b3d8c",
      wash: "#f1ecf8",
      solid: "#5b3d8c",
    },
    audience: "Drug designers, structural biologists, and R&D leads exploring modern design surfaces.",
    pillars: [
      {
        title: "See the structure",
        body: "Immersive and desktop views that make spatial relationships legible — so design conversations stay grounded in the molecule.",
      },
      {
        title: "A disciplined loop",
        body: "Design, evaluate, learn, repeat — with tooling that keeps the economics and decisions of each cycle honest.",
      },
      {
        title: "Software-first stage",
        body: "A design platform and visualization surface today. Not a wet-lab robotics claim; not a clinical product.",
      },
    ],
    promises: [
      "Structure-guided design posture",
      "Immersive + desktop entry points",
      "Clear non-goals: no therapeutic claims in the UI",
    ],
    statusNote: "Design platform under active development (Stage A software surface).",
    disclaimer:
      "Research and design software. Not a medical device. Not a substitute for regulated laboratory processes. No therapeutic claims.",
    portfolioOrigin: DRUG_DESIGN_ORIGIN,
    ctaPrimary: {
      label: "Request a design-lab conversation",
      href: "mailto:hello@flmanbiosci.net?subject=Next-gen%20drug%20development",
    },
    ctaSecondary: { label: "Company home", href: "/" },
  },
};

export const PRODUCT_LIST: ProductPage[] = [
  PRODUCTS.u4u,
  PRODUCTS["next-gen-drug-development"],
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
