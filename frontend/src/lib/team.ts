/**
 * Public company team roster for flmanbiosci.net.
 *
 * Public founder titles: flmanbiosci-ops team-assets.md (operator-hard).
 * Narrative bios: only after t-fmbweb-team-bios has written OK — until
 * then `blurb` stays empty. Do not invent copy here.
 *
 * Do not publish equity % or internal reserve semantics on the marketing site.
 */

export type TeamTier = "founder" | "contributor" | "advisor";

export type TeamMember = {
  id: string;
  name: string;
  role: string;
  /** Empty until t-fmbweb-team-bios lands approved copy. */
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

/** Founding team — public marketing roles only; no equity % on this page. */
export const FOUNDERS: TeamMember[] = [
  {
    id: "noah",
    name: "Noah T. Jones",
    role: "Founder & CEO",
    blurb: "",
    tier: "founder",
    nucleateActivator: true,
    ...photo("noah"),
    initials: "NJ",
  },
  {
    id: "curtis",
    name: "Curtis Dearing",
    role: "Chief Vision Officer & CPO of PeptOdyssey",
    blurb: "",
    tier: "founder",
    nucleateActivator: true,
    ...photo("curtis"),
    initials: "CD",
  },
  {
    id: "garrett",
    name: "Garrett Knotts",
    role: "Founder",
    blurb: "",
    tier: "founder",
    nucleateActivator: true,
    ...photo("garrett"),
    initials: "GK",
  },
  {
    id: "michael",
    name: "Michael MacNair",
    role: "Chemistry & Delivery",
    blurb: "",
    tier: "founder",
    nucleateActivator: true,
    ...photo("michael"),
    initials: "MM",
  },
  {
    id: "jacob",
    name: "Jacob Davis",
    role: "Bioinformatics",
    blurb: "",
    tier: "founder",
    nucleateActivator: true,
    ...photo("jacob"),
    initials: "JD",
  },
  {
    id: "tyler",
    name: "Tyler Kopf",
    role: "Clinical & Operations",
    blurb: "",
    tier: "founder",
    nucleateActivator: true,
    ...photo("tyler"),
    initials: "TK",
  },
];

/**
 * Nucleate Activator / program contributors and extended team.
 * Names already public on /team; roles are short labels, not bios.
 */
export const CONTRIBUTORS: TeamMember[] = [
  {
    id: "sasank",
    name: "Sasank Desaraju",
    role: "Clinical anchor · PeptOdyssey contributor",
    blurb: "",
    tier: "contributor",
    nucleateActivator: true,
    initials: "SD",
  },
  {
    id: "kayla",
    name: "Kayla Schwartz",
    role: "Safety & contraindications",
    blurb: "",
    tier: "contributor",
    nucleateActivator: true,
    initials: "KS",
  },
  {
    id: "rocky",
    name: "Rocky Truong",
    role: "Oncology genetics · VR structural biochemistry",
    blurb: "",
    tier: "contributor",
    nucleateActivator: true,
    initials: "RT",
  },
  {
    id: "min",
    name: "Min Young Park",
    role: "Metabolism · MitoFocus",
    blurb: "",
    tier: "contributor",
    nucleateActivator: true,
    initials: "MP",
  },
  {
    id: "delaney",
    name: "Delaney Ding",
    role: "Clinical & translational strategy",
    blurb: "",
    tier: "contributor",
    nucleateActivator: true,
    initials: "DD",
  },
  {
    id: "christopher",
    name: "Christopher Marais",
    role: "Activator contributor",
    blurb: "",
    tier: "contributor",
    nucleateActivator: true,
    initials: "CM",
  },
  {
    id: "hampton",
    name: "Hampton Copeland",
    role: "Engineering lead",
    blurb: "",
    tier: "contributor",
    nucleateActivator: true,
    initials: "HC",
  },
  {
    id: "jeran",
    name: "Jeran Fox",
    role: "Marketing & growth",
    blurb: "",
    tier: "contributor",
    nucleateActivator: true,
    initials: "JF",
  },
  {
    id: "ty",
    name: "Ty Dearing",
    role: "Contributor",
    blurb: "",
    tier: "contributor",
    initials: "TD",
  },
];

export const ADVISORS: TeamMember[] = [
  {
    id: "giuseppina",
    name: "Giuseppina Sannino",
    role: "Commercialization advisor",
    blurb: "",
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
