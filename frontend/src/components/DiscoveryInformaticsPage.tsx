import Link from "next/link";
import { CompanyChrome, companySerif } from "@/components/CompanyChrome";
import { LabConsole } from "@/components/LabConsole";
import { type ProductPage } from "@/lib/products";

type Props = { product: ProductPage };

const LOOP = [
  {
    n: "01",
    title: "Ask",
    body: "A PI question lands in the OS. The product is the loop that follows.",
  },
  {
    n: "02",
    title: "Route",
    body: "Send the ask to the smallest matching skill.",
  },
  {
    n: "03",
    title: "Normalize IDs",
    body: "Resolve entities to public identifiers before any lookup. The PI decides occupancy.",
  },
  {
    n: "04",
    title: "Smallest skill set",
    body: "Public-API skills only. Independent lanes may run in parallel. Shared-state work stays serial.",
  },
  {
    n: "05",
    title: "Artifacts + METHODS + cannots",
    body: "Versioned TSV/JSON/figures, a METHODS record (IDs, dates, API versions), and an explicit cannots list.",
  },
  {
    n: "06",
    title: "Dual-copy desk",
    body: "Small reports land on the customer desk and, when the ask is that corpus, the RAG sidecar. One corpus per bot.",
  },
  {
    n: "07",
    title: "Journal",
    body: "When the workspace is a plan task, append a note. Strategy that commits the bench escalates to the PI.",
  },
] as const;

const LANES = [
  {
    kicker: "Lanes",
    title: "Parallel only when independent",
    body: "Delegate separate work when the lanes are independent. Serial is the default.",
  },
  {
    kicker: "Worktrees",
    title: "Exclusive trees, exclusive paths",
    body: "Each lane gets its own worktree.",
  },
  {
    kicker: "Public APIs",
    title: "Skills that hit public endpoints",
    body: "Official scripts, versioned APIs. Cannots are first-class output.",
  },
  {
    kicker: "Honesty bar",
    title: "METHODS and cannots, every time",
    body: "Named artifact paths. Provenance (public URL vs operator-saved PDF vs missing). Cannots are first-class output.",
  },
] as const;

const SKUS = [
  {
    code: "DI-OS Core",
    includes:
      "Science-agent workbench profile, research router, artifact / METHODS / cannots contract, exclusive worktrees.",
  },
  {
    code: "DI-RAG Sidecar",
    includes:
      "One-corpus RAG sidecar: ingest inbox, critic, local embeddings, localhost MCP.",
  },
  {
    code: "DI-Jail",
    includes:
      "Tenant factory: isolated cwd, pairing allow-list, exclusive worktrees.",
  },
  {
    code: "DI-ELN Logistics",
    includes:
      "Campaign folders, procedure skeleton, week PDF, calendar lock as a proposal.",
  },
] as const;

export function DiscoveryInformaticsPage({ product }: Props) {
  return (
    <CompanyChrome active="products">
      <div className="bg-[#f5f4f0] text-[#0d1117]">
        {/* Hero */}
        <section className="relative overflow-hidden border-b border-[#dbd9d3]">
          <div
            className="pointer-events-none absolute inset-0"
            aria-hidden
            style={{
              background:
                "linear-gradient(180deg, #e8f4ee 0%, #f5f4f0 58%, #f5f4f0 100%)",
            }}
          />
          <div className="relative mx-auto grid max-w-[1180px] gap-12 px-6 py-14 md:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)] md:items-end md:px-7 md:py-20">
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[#1a6b4a]">
                {product.eyebrow}
              </p>
              <h1
                className="mt-4 text-[2.4rem] leading-[1.05] tracking-tight md:text-5xl lg:text-[3.5rem]"
                style={companySerif}
              >
                Discovery Informatics
              </h1>
              <p
                className="mt-4 max-w-xl text-xl leading-snug text-[#0f4530] md:text-2xl"
                style={companySerif}
              >
                {product.tagline}
              </p>
              <p className="mt-5 max-w-xl text-base leading-relaxed text-[#3a3f4a] md:text-lg">
                {product.description}
              </p>
              <p className="mt-4 max-w-xl text-sm leading-relaxed text-[#3a3f4a]">
                {product.whyItMatters}
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <a
                  href={product.ctaPrimary.href}
                  className="inline-flex min-h-11 items-center gap-2 rounded-full bg-[#1a6b4a] px-6 py-3 text-sm font-semibold text-white hover:bg-[#0f4530]"
                >
                  {product.ctaPrimary.label}
                  <span aria-hidden>→</span>
                </a>
                <Link
                  href={product.ctaSecondary.href}
                  className="inline-flex min-h-11 items-center rounded-full border border-[#dbd9d3] bg-white px-6 py-3 text-sm font-semibold text-[#0d1117] hover:border-[#1a6b4a]/45"
                >
                  {product.ctaSecondary.label}
                </Link>
              </div>
              <p className="mt-5 max-w-xl text-xs leading-relaxed text-[#6b7280]">
                <span className="font-medium text-[#3a3f4a]">Status: </span>
                {product.statusNote} Mailto opens your mail client; inbound
                routing on that address may still be unset.
              </p>
            </div>

            <figure className="rounded-none border border-[#dbd9d3] bg-white p-5 shadow-[6px_6px_0_0_#1a6b4a]">
              <figcaption className="font-mono text-[11px] font-medium uppercase tracking-[0.14em] text-[#1a6b4a]">
                Loop · Wave 0
              </figcaption>
              <LoopDiagram />
            </figure>
          </div>
        </section>

        {/* The loop */}
        <section className="border-b border-[#dbd9d3] bg-white py-16 md:py-20">
          <div className="mx-auto max-w-[1180px] px-6 md:px-7">
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[#1a6b4a]">
              The loop
            </p>
            <h2
              className="mt-2 max-w-3xl text-3xl leading-tight md:text-4xl"
              style={companySerif}
            >
              Ask → evidence → artifacts. Then say what you cannot.
            </h2>
            <p className="mt-4 max-w-2xl text-base leading-relaxed text-[#3a3f4a]">
              Discovery Informatics is a jailed science-agent operating system.
              The payload is the method — routed public evidence, versioned
              files, METHODS, and cannots.
            </p>
            <ol className="mt-12 grid gap-0 md:grid-cols-2">
              {LOOP.map((step, i) => (
                <li
                  key={step.n}
                  className={`flex gap-4 border-[#edecea] py-6 ${
                    i < LOOP.length - 1 ? "border-b" : ""
                  } ${i % 2 === 0 ? "md:pr-8" : "md:border-l md:pl-8"} ${
                    i >= LOOP.length - 2 ? "md:border-b-0" : "md:border-b"
                  }`}
                >
                  <span
                    className="mt-0.5 shrink-0 font-mono text-sm font-medium text-[#1a6b4a]"
                    aria-hidden
                  >
                    {step.n}
                  </span>
                  <div>
                    <h3 className="text-lg text-[#0d1117]" style={companySerif}>
                      {step.title}
                    </h3>
                    <p className="mt-2 text-sm leading-relaxed text-[#3a3f4a]">
                      {step.body}
                    </p>
                  </div>
                </li>
              ))}
            </ol>
          </div>
        </section>

        {/* How agents work */}
        <section className="border-b border-[#dbd9d3] bg-[#f5f4f0] py-16 md:py-20">
          <div className="mx-auto max-w-[1180px] px-6 md:px-7">
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[#1a6b4a]">
              How agents work
            </p>
            <h2
              className="mt-2 max-w-3xl text-3xl leading-tight md:text-4xl"
              style={companySerif}
            >
              Parallel lanes. Exclusive worktrees. Public APIs. Then METHODS.
            </h2>
            <p className="mt-4 max-w-2xl text-base leading-relaxed text-[#3a3f4a]">
              What we actually run is generic: independent lanes, tenant jail,
              localhost RAG sidecar, public-API skills. The customer rsyncs
              their own desk.
            </p>

            <WorktreeLanes />

            <div className="mt-10 grid gap-px bg-[#dbd9d3] sm:grid-cols-2">
              {LANES.map((lane) => (
                <article
                  key={lane.kicker}
                  className="bg-[#f5f4f0] p-6 md:p-8"
                >
                  <p className="font-mono text-[11px] font-medium uppercase tracking-[0.14em] text-[#1a6b4a]">
                    {lane.kicker}
                  </p>
                  <h3
                    className="mt-2 text-xl text-[#0d1117]"
                    style={companySerif}
                  >
                    {lane.title}
                  </h3>
                  <p className="mt-3 text-sm leading-relaxed text-[#3a3f4a]">
                    {lane.body}
                  </p>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* SKUs */}
        <section className="border-b border-[#dbd9d3] bg-white py-16 md:py-20">
          <div className="mx-auto max-w-[1180px] px-6 md:px-7">
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div>
                <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[#1a6b4a]">
                  Wave 0 names
                </p>
                <h2
                  className="mt-2 text-3xl md:text-4xl"
                  style={companySerif}
                >
                  SKUs, unpriced.
                </h2>
              </div>
              <p className="max-w-sm text-sm leading-relaxed text-[#6b7280]">
                Names for the productization wave. Unpriced SKUs.
              </p>
            </div>
            <div className="mt-10 overflow-x-auto">
              <table className="w-full min-w-[640px] border-collapse text-left text-sm">
                <caption className="sr-only">
                  Discovery Informatics Wave 0 SKUs, unpriced
                </caption>
                <thead>
                  <tr className="border-b border-[#0d1117] text-[11px] font-bold uppercase tracking-[0.12em] text-[#6b7280]">
                    <th scope="col" className="py-3 pr-4 font-bold">
                      SKU
                    </th>
                    <th scope="col" className="py-3 pr-4 font-bold">
                      Includes
                    </th>
                    <th scope="col" className="py-3 text-right font-bold">
                      Price
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {SKUS.map((sku) => (
                    <tr key={sku.code} className="border-b border-[#edecea]">
                      <th
                        scope="row"
                        className="py-4 pr-4 font-mono text-sm font-medium text-[#0d1117]"
                      >
                        {sku.code}
                      </th>
                      <td className="py-4 pr-4 align-top leading-relaxed text-[#3a3f4a]">
                        {sku.includes}
                      </td>
                      <td className="py-4 text-right align-top font-mono text-xs uppercase tracking-wide text-[#6b7280]">
                        Unpriced
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* Lab jail (Wave 0.5) */}
        <section
          id="lab"
          className="scroll-mt-24 border-b border-[#dbd9d3] bg-[#f5f4f0] py-16 md:py-20"
        >
          <div className="mx-auto max-w-[1180px] px-6 md:px-7">
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[#1a6b4a]">
              Wave 0.5 · Lab jail
            </p>
            <h2 className="mt-2 text-3xl md:text-4xl" style={companySerif}>
              A containerized generic lab profile.
            </h2>
            <p className="mt-4 max-w-2xl text-base leading-relaxed text-[#3a3f4a]">
              <code className="font-mono text-sm">yue-lab</code> is one tenant
              of this class. The FMB demo is an empty Hermes lab jail
              (bioinformatics skills) on the hwcopeland cluster. POST requires
              a shared token.
            </p>
            <ul className="mt-6 max-w-2xl list-disc space-y-2 pl-5 text-sm text-[#3a3f4a]">
              <li>
                Host:{" "}
                <a
                  className="font-medium text-[#1a6b4a] hover:underline"
                  href="https://lab.flmanbiosci.net/"
                  rel="noopener noreferrer"
                >
                  lab.flmanbiosci.net
                </a>{" "}
                (HTTPRoute on theswamp — live after Flux + image). Health:{" "}
                <code className="font-mono text-xs">GET /health</code>
              </li>
              <li>
                Isolation: pod is the jail.
              </li>
              <li>
                Token via{" "}
                <a className="text-[#1a6b4a] hover:underline" href="mailto:hello@flmanbiosci.net">
                  hello@flmanbiosci.net
                </a>
                . Empty token → POST 401.
              </li>
            </ul>
            <a
              href="/owui/"
              rel="noopener noreferrer"
              className="mt-8 mr-3 inline-flex min-h-11 items-center rounded-full bg-[#1a6b4a] px-6 py-3 text-sm font-semibold text-white hover:bg-[#0f4530]"
            >
              Open lab chat →
            </a>
            <a
              href="#lab-console"
              className="mt-8 inline-flex min-h-11 items-center rounded-full border border-[#1a6b4a] px-6 py-3 text-sm font-semibold text-[#1a6b4a] hover:bg-[#e8f3ee]"
            >
              One-shot console on this page
            </a>
            <LabConsole />
          </div>
        </section>

        {/* Related + disclaimer */}
        <section className="border-b border-[#dbd9d3] bg-[#0f4530] py-16 text-[#f5f4f0] md:py-20">
          <div className="mx-auto grid max-w-[1180px] gap-10 px-6 md:grid-cols-[1.1fr_0.9fr] md:px-7">
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-[#a8d5c2]">
                Related product
              </p>
              <h2 className="mt-3 text-3xl md:text-4xl" style={companySerif}>
                Protein Chemistry is the design surface.
              </h2>
              <p className="mt-4 max-w-xl text-base leading-relaxed text-[#d7ebe1]">
                Structure visualization and a simulated design–build–test–learn
                loop live on a different page. The two products stay separate.
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <Link
                  href="/products/next-gen-drug-development"
                  className="inline-flex min-h-11 items-center rounded-full bg-white px-6 py-3 text-sm font-semibold text-[#0f4530] hover:bg-[#f5f4f0]"
                >
                  Protein Chemistry →
                </Link>
                <a
                  href={product.ctaPrimary.href}
                  className="inline-flex min-h-11 items-center rounded-full border border-white/30 px-6 py-3 text-sm font-semibold text-white hover:border-white/60"
                >
                  {product.ctaPrimary.label}
                </a>
              </div>
            </div>
            <aside className="border border-white/15 bg-white/5 p-6">
              <h3 className="text-lg" style={companySerif}>
                Disclaimer
              </h3>
              <p className="mt-3 text-sm leading-relaxed text-[#d7ebe1]">
                {product.disclaimer}
              </p>
              <p className="mt-4 text-xs leading-relaxed text-[#a8d5c2]">
                Contact is a mailto to hello@flmanbiosci.net.
              </p>
            </aside>
          </div>
        </section>
      </div>
    </CompanyChrome>
  );
}

function LoopDiagram() {
  const nodes = [
    "ask",
    "route",
    "IDs",
    "skills",
    "artifacts",
    "desk",
    "journal",
  ];
  return (
    <svg
      viewBox="0 0 320 220"
      role="img"
      aria-label="Seven-step loop from ask through journal"
      className="mt-4 h-auto w-full"
    >
      {nodes.map((label, i) => {
        const y = 18 + i * 28;
        return (
          <g key={label}>
            {i < nodes.length - 1 ? (
              <line
                x1="16"
                y1={y + 8}
                x2="16"
                y2={y + 28}
                stroke="#1a6b4a"
                strokeWidth="1.5"
              />
            ) : null}
            <rect x="8" y={y} width="16" height="16" fill="#1a6b4a" />
            <text
              x="36"
              y={y + 13}
              fontFamily="'DM Mono', ui-monospace, monospace"
              fontSize="13"
              fill="#0d1117"
            >
              {label}
            </text>
            <rect
              x={120}
              y={y + 4}
              width={170 - i * 8}
              height="8"
              fill={i === 4 ? "#1a6b4a" : "#e8f4ee"}
            />
          </g>
        );
      })}
    </svg>
  );
}

function WorktreeLanes() {
  return (
    <div className="mt-10 border border-[#dbd9d3] bg-white p-5 md:p-6">
      <p className="font-mono text-[11px] font-medium uppercase tracking-[0.14em] text-[#1a6b4a]">
        Exclusive worktrees
      </p>
      <ul className="mt-4 space-y-3" role="list">
        {[
          { lane: "lane-a", path: ".worktrees/ask-route-ids" },
          { lane: "lane-b", path: ".worktrees/public-api-lookup" },
          { lane: "lane-c", path: ".worktrees/methods-cannots" },
        ].map((row) => (
          <li key={row.lane} className="flex items-center gap-3">
            <span className="w-16 shrink-0 font-mono text-xs text-[#6b7280]">
              {row.lane}
            </span>
            <span className="h-2 flex-1 bg-[#1a6b4a]" aria-hidden />
            <span className="min-w-0 truncate font-mono text-xs text-[#0d1117]">
              {row.path}
            </span>
          </li>
        ))}
      </ul>
      <p className="mt-4 border-t border-[#edecea] pt-3 font-mono text-xs text-[#3a3f4a]">
        merge ← METHODS + cannots · exclusive worktrees
      </p>
    </div>
  );
}
