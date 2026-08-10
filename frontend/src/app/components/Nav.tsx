import Link from "next/link";
import { COMPANY_ORIGIN, PRODUCT_PRIVACY_PATH } from "@/lib/site";

export function Nav() {
  return (
    <header className="bg-[#0d1117] border-b border-[#1a6b4a]/30">
      <div className="mx-auto max-w-5xl px-4 h-14 flex items-center justify-between gap-4">
        <div className="flex items-center gap-4 min-w-0">
          <Link
            href="/peptodyssey"
            className="flex items-center gap-2.5 hover:opacity-90 transition-opacity shrink-0"
          >
            <span className="text-[#2d8f61] text-lg">&#x2726;</span>
            <span
              className="text-white text-lg tracking-tight"
              style={{ fontFamily: "'DM Serif Display', serif" }}
            >
              PeptOdyssey
            </span>
          </Link>
          <a
            href={COMPANY_ORIGIN}
            className="hidden sm:inline text-xs text-zinc-500 hover:text-zinc-300 transition-colors truncate"
          >
            Florida Man Bioscience
          </a>
        </div>

        <nav className="flex items-center gap-4 sm:gap-5 text-sm flex-wrap justify-end">
          <Link
            href="/peptodyssey/analyze"
            className="text-zinc-400 hover:text-white transition-colors"
          >
            Analyze
          </Link>
          <Link
            href="/jobs"
            className="text-zinc-400 hover:text-white transition-colors"
          >
            History
          </Link>
          <Link
            href="/tracking"
            className="text-zinc-400 hover:text-white transition-colors"
          >
            Tracking
          </Link>
          <Link
            href="/regulatory"
            className="hidden md:inline text-zinc-400 hover:text-white transition-colors"
          >
            Regulatory
          </Link>
          <Link
            href="/study"
            className="hidden md:inline text-zinc-400 hover:text-white transition-colors"
          >
            Study
          </Link>
          <Link
            href="/faq"
            className="text-zinc-400 hover:text-white transition-colors"
          >
            FAQ
          </Link>
          <Link
            href={PRODUCT_PRIVACY_PATH}
            className="hidden lg:inline text-zinc-400 hover:text-white transition-colors"
          >
            Privacy
          </Link>
        </nav>
      </div>
    </header>
  );
}
