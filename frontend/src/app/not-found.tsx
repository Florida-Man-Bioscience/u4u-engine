import Link from "next/link";
import { CompanyChrome, companySerif } from "@/components/CompanyChrome";

export default function NotFound() {
  return (
    <CompanyChrome>
      <div className="mx-auto max-w-[720px] px-6 py-24 md:px-7">
        <p className="text-xs font-bold uppercase tracking-[0.14em] text-[#1a6b4a]">
          404
        </p>
        <h1
          className="mt-2 text-4xl text-[#0d1117] md:text-5xl"
          style={companySerif}
        >
          This page is not on the map.
        </h1>
        <p className="mt-4 text-[#3a3f4a]">
          The shipping product is PeptOdyssey. Lab software lives under CytoGate.
          Or go back to the company home.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link
            href="/"
            className="inline-flex rounded-full bg-[#1a6b4a] px-5 py-2.5 text-sm font-semibold text-white hover:bg-[#0f4530]"
          >
            Company home
          </Link>
          <Link
            href="/peptodyssey"
            className="inline-flex rounded-full border border-[#dbd9d3] px-5 py-2.5 text-sm font-semibold text-[#0d1117] hover:border-[#1a6b4a]/40"
          >
            PeptOdyssey
          </Link>
          <Link
            href="/products/cytogate"
            className="inline-flex rounded-full border border-[#dbd9d3] px-5 py-2.5 text-sm font-semibold text-[#0d1117] hover:border-[#1a6b4a]/40"
          >
            CytoGate
          </Link>
        </div>
      </div>
    </CompanyChrome>
  );
}
