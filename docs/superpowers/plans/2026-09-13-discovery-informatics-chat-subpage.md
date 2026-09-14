# Discovery Informatics Chat Subpage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the Discovery Informatics multi-shot console from the product page into `/products/discovery-informatics/chat` while preserving its live API and lit-review behavior.

**Architecture:** Keep `/products/discovery-informatics` as the marketing/product surface and create a dedicated App Router page at `/products/discovery-informatics/chat`. The new page renders the existing `LabConsole` client component inside the existing `CompanyChrome`; API route handlers and the di-lab deployment remain unchanged. The retired `/owui` route redirects to the new canonical chat page.

**Tech Stack:** Next.js App Router, React/TypeScript, Tailwind utility classes, existing `LabConsole`, same-origin `/api/lab/*` route handlers.

## Global Constraints

- Ship target remains `/home/noahtjones/u4u-engine/frontend`.
- Keep `/api/lab/turn`, `/api/lab/health`, and `/api/lab/tools/paper-decomposition/admit` unchanged.
- Preserve multi-shot `messages[]` behavior and automatic `lit-review` preload.
- Do not open or modify IAC; `lab-chat.flmanbiosci.net` remains separate.
- Do not restore or extend `/owui` Open WebUI path surgery.
- Public marketing copy stays positive and avoids technical implementation dumps outside the chat page.

---

### Task 1: Add the canonical chat page

**Files:**
- Create: `frontend/src/app/(marketing)/products/discovery-informatics/chat/page.tsx`
- Modify: `frontend/src/app/owui/[[...path]]/route.ts`

**Interfaces:**
- Consumes: `LabConsole`, `CompanyChrome`, and the existing Discovery Informatics product route.
- Produces: canonical URL `/products/discovery-informatics/chat`; legacy `/owui` redirects there.

- [x] Create a server page with metadata title `Discovery Informatics Lab`, description describing the multi-shot lab console, and canonical URL `/products/discovery-informatics/chat`.
- [x] Render a back link to `/products/discovery-informatics`, a concise lab heading/status explanation, and `<LabConsole />`.
- [x] Change the `/owui` redirect target from the hash anchor to `/products/discovery-informatics/chat`.

### Task 2: Remove the embedded console and link to the subpage

**Files:**
- Modify: `frontend/src/components/DiscoveryInformaticsPage.tsx`

**Interfaces:**
- Consumes: the existing lab-jail marketing section.
- Produces: product page CTA linking to `/products/discovery-informatics/chat` without rendering the console inline.

- [x] Remove the `LabConsole` import and inline render.
- [x] Replace the hash-anchor CTA with a `next/link` CTA to the new chat page.
- [x] Keep the lab-jail explanation and dedicated-host/IAC note on the marketing page.

### Task 3: Verify and ship

**Files:**
- Modify: `docs/superpowers/plans/2026-09-13-discovery-informatics-chat-subpage.md`

- [x] Run `npx tsc --noEmit` in `frontend/`.
- [x] Run `npm run build` in `frontend/` and confirm `/products/discovery-informatics/chat` builds.
- [ ] Curl the live page after rollout and verify the new route contains the chat page and the old `/owui` target resolves to it.
- [ ] Commit the focused changes and open a PR against `main`.
