import type { Metadata } from "next";
import Link from "next/link";
import { CompanyChrome, companySerif } from "@/components/CompanyChrome";
import { LabConsole } from "@/components/LabConsole";

const CHAT_PATH = "/products/discovery-informatics/chat";

export const metadata: Metadata = {
  title: "Discovery Informatics Lab",
  description:
    "A multi-shot Discovery Informatics lab console with the lit-review pipeline preloaded.",
  alternates: { canonical: CHAT_PATH },
  openGraph: {
    title: "Discovery Informatics Lab — Florida Man Bioscience",
    description:
      "A multi-shot Discovery Informatics lab console with the lit-review pipeline preloaded.",
    url: CHAT_PATH,
    siteName: "Florida Man Bioscience",
    type: "website",
    images: [{ url: "/assets/img/mark.png" }],
  },
};

export default function DiscoveryInformaticsChatPage() {
  return (
    <CompanyChrome active="products">
      <main className="bg-[#f5f4f0] text-[#0d1117]">
        <section className="border-b border-[#dbd9d3] bg-white">
          <div className="mx-auto max-w-[1180px] px-6 py-12 md:px-7 md:py-16">
            <Link
              href="/products/discovery-informatics"
              className="font-mono text-xs font-medium uppercase tracking-[0.14em] text-[#1a6b4a] hover:underline"
            >
              ← Discovery Informatics
            </Link>
            <p className="mt-10 text-[11px] font-bold uppercase tracking-[0.18em] text-[#1a6b4a]">
              Lab console · Wave 0.5
            </p>
            <h1
              className="mt-3 max-w-3xl text-4xl leading-tight md:text-6xl"
              style={companySerif}
            >
              Discovery Informatics, in conversation.
            </h1>
            <p className="mt-5 max-w-2xl text-base leading-relaxed text-[#3a3f4a] md:text-lg">
              Continue an ask across turns. The lab keeps the thread in this
              page and preloads the lit-review pipeline for paper formalization.
            </p>
            <p className="mt-4 max-w-2xl text-sm leading-relaxed text-[#6b7280]">
              A shared token gates the lab. Provider keys stay in the jail or
              can be supplied for one turn only.
            </p>
          </div>
        </section>
        <section className="mx-auto max-w-[1180px] px-6 py-10 md:px-7 md:py-16">
          <LabConsole />
        </section>
      </main>
    </CompanyChrome>
  );
}
