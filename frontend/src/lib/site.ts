/** Canonical public hosts for FMB / PeptOdyssey. */
export const COMPANY_HOST = "flmanbiosci.net";
export const PRODUCT_HOST = "peptodyssey.flmanbiosci.net";
export const PRODUCT_API_HOST = "api.peptodyssey.flmanbiosci.net";

export const COMPANY_ORIGIN = `https://${COMPANY_HOST}`;
export const PRODUCT_ORIGIN = `https://${PRODUCT_HOST}`;
/** Direct API (no browser SSO). Prefer for HealthKit / scripts. */
export const PRODUCT_API_ORIGIN = `https://${PRODUCT_API_HOST}`;

/** Same-origin API prefix when the browser is on the product host. */
export const PRODUCT_API_PATH = "/api/v1";

export const PRODUCT_PRIVACY_PATH = "/privacy";
export const PRODUCT_PRIVACY_URL = `${PRODUCT_ORIGIN}${PRODUCT_PRIVACY_PATH}`;
/** Frozen legacy URL — must keep working via 301. */
export const LEGACY_PRIVACY_URL = `${COMPANY_ORIGIN}/peptodyssey/privacy`;

export const CYTOGATE_HOST = "cytogate.flmanbiosci.net";
export const U4U_PRIVACY_HOST = "u4u-privacy.flmanbiosci.net";
export const CYTOGATE_ORIGIN = `https://${CYTOGATE_HOST}`;
export const U4U_PRIVACY_ORIGIN = `https://${U4U_PRIVACY_HOST}`;
