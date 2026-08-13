/** Canonical public hosts for FMB / PeptOdyssey. */

export const COMPANY_HOST = "flmanbiosci.net";
export const PRODUCT_HOST = "peptodyssey.flmanbiosci.net";

export const COMPANY_ORIGIN = `https://${COMPANY_HOST}`;
export const PRODUCT_ORIGIN = `https://${PRODUCT_HOST}`;

/**
 * Canonical API shape for FMB product hosts: `https://{host}/api/v1`.
 * Prefer same-origin on the product host (valid TLS under *.flmanbiosci.net;
 * no double-subdomain api.* host).
 */
export const PRODUCT_API_PATH = "/api/v1";
export const PRODUCT_API_ORIGIN = `${PRODUCT_ORIGIN}${PRODUCT_API_PATH}`;

/** @deprecated Use PRODUCT_HOST + PRODUCT_API_PATH; kept for call-site clarity. */
export const PRODUCT_API_HOST = PRODUCT_HOST;

export const PRODUCT_PRIVACY_PATH = "/privacy";
export const PRODUCT_PRIVACY_URL = `${PRODUCT_ORIGIN}${PRODUCT_PRIVACY_PATH}`;
/** Frozen legacy URL — must keep working via 301. */
export const LEGACY_PRIVACY_URL = `${COMPANY_ORIGIN}/peptodyssey/privacy`;

/** Legacy dual-route (unprefixed engine paths). Prefer PRODUCT_API_ORIGIN. */
export const LEGACY_API_HOST = "api.flmanbiosci.net";
export const LEGACY_API_ORIGIN = `https://${LEGACY_API_HOST}`;

export const CYTOGATE_HOST = "cytogate.flmanbiosci.net";
export const U4U_PRIVACY_HOST = "u4u-privacy.flmanbiosci.net";
export const NANODISK_HOST = "nanodisk.flmanbiosci.net";
export const DRUG_DESIGN_HOST = "drug-design.flmanbiosci.net";
export const CYTOGATE_ORIGIN = `https://${CYTOGATE_HOST}`;
export const U4U_PRIVACY_ORIGIN = `https://${U4U_PRIVACY_HOST}`;
export const NANODISK_ORIGIN = `https://${NANODISK_HOST}`;
export const DRUG_DESIGN_ORIGIN = `https://${DRUG_DESIGN_HOST}`;
export const PROTEIN_CHEMISTRY_URL = `${DRUG_DESIGN_ORIGIN}/protein-chemistry/`;
