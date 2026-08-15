/**
 * Public company team roster for flmanbiosci.net.
 *
 * Sources (ops, not legal cap table):
 * - fmb-company/company/team.md (founders)
 * - PeptidIQ_Pitch_Deck_2026-05-07.pptx “Why Us?”
 * - FloridaManBioscience_Workshop2.pdf “Meet the team”
 * - Operator direction: include full Nucleate Activator contributors
 *   (Rocky, Kayla, Min, Sasank, …)
 *
 * Do not publish equity % or internal reserve semantics on the marketing site.
 */

export type TeamTier = "founder" | "contributor" | "advisor";

export type TeamMember = {
  id: string;
  name: string;
  role: string;
  blurb: string;
  tier: TeamTier;
  /** Nucleate Florida / Activator cohort (2026 launch materials). */
  nucleateActivator?: boolean;
  img?: string;
  imgFallback?: string;
  initials: string;
};

function photo(slug: string): Pick<TeamMember, "img" | "imgFallback"> {
  return {
    img: `/assets/img/${slug}.webp`,
    imgFallback: `/assets/img/${slug}.jpg`,
  };
}

/** Founding team — order: CEO, CVO, core, reserved founders. */
export const FOUNDERS: TeamMember[] = [
  {
    id: "noah",
    name: "Noah T. Jones",
    role: "Founder & CEO",
    blurb:
      "Builds the engine and app foundations. Bioinformatics, pipeline architecture, and company operations.",
    tier: "founder",
    nucleateActivator: true,
    ...photo("noah"),
    initials: "NJ",
  },
  {
    id: "curtis",
    name: "Curtis Dearing",
    role: "Co-founder · CVO · CPO, PeptOdyssey",
    blurb:
      "Chief Vision Officer and PeptOdyssey product lead. Core builder of the U4U engine and patient-facing product.",
    tier: "founder",
    nucleateActivator: true,
    ...photo("curtis"),
    initials: "CD",
  },
  {
    id: "garrett",
    name: "Garrett Knotts",
    role: "Co-founder · Omics",
    blurb:
      "Core founder. Omics and mitochondria-focused product threads (including MitoFocus).",
    tier: "founder",
    nucleateActivator: true,
    ...photo("garrett"),
    initials: "GK",
  },
  {
    id: "michael",
    name: "Michael MacNair",
    role: "Co-founder · Structural biology",
    blurb:
      "Core founder. Structural biochemistry and VR structural-biochemistry platform leadership.",
    tier: "founder",
    nucleateActivator: true,
    ...photo("michael"),
    initials: "MM",
  },
  {
    id: "jacob",
    name: "Jacob Davis",
    role: "Founder · Bioinformatics",
    blurb:
      "Founder. Bioinformatics and immunology; Neurocreatine project leadership.",
    tier: "founder",
    nucleateActivator: true,
    ...photo("jacob"),
    initials: "JD",
  },
  {
    id: "tyler",
    name: "Tyler Kopf",
    role: "Founder · Clinical & operations",
    blurb:
      "Founder. Clinical and operations; skunkworks and program execution.",
    tier: "founder",
    nucleateActivator: true,
    ...photo("tyler"),
    initials: "TK",
  },
];

/**
 * Nucleate Activator / program contributors and extended team.
 * Full names and public roles from Activator pitch + workshop materials.
 */
export const CONTRIBUTORS: TeamMember[] = [
  {
    id: "sasank",
    name: "Sasank Desaraju",
    role: "Clinical anchor · U4U contributor",
    blurb:
      "MD/PhD student, University of Florida. Clinical link and U4U intelligence; engine contributor.",
    tier: "contributor",
    nucleateActivator: true,
    initials: "SD",
  },
  {
    id: "kayla",
    name: "Kayla Schwartz",
    role: "Safety & contraindications",
    blurb:
      "MD-PhD student, University of Miami. Safety / contraindication layer for genotype-aware peptide protocols.",
    tier: "contributor",
    nucleateActivator: true,
    initials: "KS",
  },
  {
    id: "rocky",
    name: "Rocky Truong",
    role: "Oncology genetics · VR structural biochemistry",
    blurb:
      "Post-doc, Moffitt Cancer Center. Oncology genetics advisor; VR structural biochemistry project lead.",
    tier: "contributor",
    nucleateActivator: true,
    initials: "RT",
  },
  {
    id: "min",
    name: "Min Young Park",
    role: "Metabolism · MitoFocus",
    blurb:
      "Metabolism biochemistry; mitochondria-focused supplement development (MitoFocus).",
    tier: "contributor",
    nucleateActivator: true,
    initials: "MP",
  },
  {
    id: "delaney",
    name: "Delaney Ding",
    role: "Clinical & translational strategy",
    blurb:
      "Clinical and public-health researcher guiding clinical and translational strategy.",
    tier: "contributor",
    nucleateActivator: true,
    initials: "DD",
  },
  {
    id: "hampton",
    name: "Hampton Copeland",
    role: "Engineering lead",
    blurb:
      "Graduate student, MTSU. Engineering lead for platform and infrastructure.",
    tier: "contributor",
    nucleateActivator: true,
    initials: "HC",
  },
  {
    id: "jeran",
    name: "Jeran Fox",
    role: "Marketing & growth",
    blurb: "GTM and growth; channel and go-to-market execution.",
    tier: "contributor",
    nucleateActivator: true,
    initials: "JF",
  },
  {
    id: "ty",
    name: "Ty Dearing",
    role: "Contributor",
    blurb: "Non-founder contributor supporting company operations and growth.",
    tier: "contributor",
    initials: "TD",
  },
];

export const ADVISORS: TeamMember[] = [
  {
    id: "giuseppina",
    name: "Giuseppina Sannino",
    role: "Commercialization advisor",
    blurb:
      "Founder & CEO, Auralis Biotech. Commercialization and strategic partnership advisor.",
    tier: "advisor",
    initials: "GS",
  },
];

/** Homepage preview: founders only (full roster on /team). */
export const TEAM_HOMEPAGE_PREVIEW = FOUNDERS;

export const ALL_TEAM: TeamMember[] = [
  ...FOUNDERS,
  ...CONTRIBUTORS,
  ...ADVISORS,
];

export const NUCLEATE_ACTIVATOR_MEMBERS = ALL_TEAM.filter(
  (m) => m.nucleateActivator,
);
