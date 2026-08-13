# Homepage content sources (t-fmbweb-homepage)

Shipped on company apex (`flmanbiosci.net/`) via PR #130 and follow-ups
(`frontend/src/app/(marketing)/page.tsx`). No invented legal/tax facts.

Detect → Design → Deliver is the public three-leg story; body copy maps the
internal Read → Predict → Report → Track → Deliver loop from company docs.

## Primary sources

| Path | Used for |
|------|----------|
| `/home/noahtjones/fmb-company/README.md` | Company one-paragraph; tagline |
| `/home/noahtjones/fmb-company/brand/README.md` | Positioning, voice (PeptOdyssey naming supersedes PeptidIQ split) |
| `/home/noahtjones/fmb-company/business-plan/01-executive-summary.md` | 5-stage loop; Stage A framing |
| `/home/noahtjones/fmb-company/regulatory/clinical-and-claims.md` | Prescriber-in-loop; no outcome guarantees |
| `/home/noahtjones/fmb-website/index.html` | Marketing hero, platform cards, programs, footer tone |
| `docs/website/IA.md` | Route targets; DDD public mapping |
| `frontend/src/lib/site.ts` | Product/portfolio host constants |
| flmanbiosci-ops skill `product-naming.md` | PeptOdyssey = one platform; PeptidIQ = legacy name only |

## Public structure (live)

1. **Who/what hero** — peptide medicine matched to the genome; clinician-in-loop disclaimer
2. **Detect → Design → Deliver** — three cards with U4U-loop mapping footnotes
3. **Platform doorways** — Engine / PeptOdyssey / Tracker → product host
4. **Other FMB surfaces** — CytoGate + u4u-privacy portfolio hosts
5. **Programs** — MSP nanodisk + CNS peptides (research-stage, no ship claim)
6. **Team** — Noah Founder & CEO; Garrett Founder; Curtis CVO & CPO of PeptOdyssey (+ others)
7. **Footer** — privacy/product links; no overclaim

## Contact email

Public mailto is currently `noahtjones@gmail.com` (intentional until Cloudflare
Email Routing lands MX for `hello@flmanbiosci.net`). Do not advertise `hello@`
until MX verifies.

## Preview

```bash
cd frontend && npm install && npm run dev
# open http://localhost:3000/
# product paths redirect on apex via middleware → peptodyssey.flmanbiosci.net
```
