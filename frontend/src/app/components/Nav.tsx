import Link from "next/link";

export function Nav() {
  return (
    <header className="bg-[#0d1117] border-b border-[#1a6b4a]/30">
      <div className="mx-auto max-w-5xl px-4 h-14 flex items-center justify-between">
        <Link
          href="/"
          className="flex items-center gap-2.5 hover:opacity-90 transition-opacity"
        >
          <span className="text-[#2d8f61] text-lg">&#x2726;</span>
          <span
            className="text-white text-lg tracking-tight"
            style={{ fontFamily: "'DM Serif Display', serif" }}
          >
            PeptOdyssey
          </span>
        </Link>

        <nav className="flex items-center gap-5 text-sm">
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
            className="text-zinc-400 hover:text-white transition-colors"
          >
            Regulatory
          </Link>
          <Link
            href="/"
            className="text-zinc-400 hover:text-white transition-colors"
          >
            New Analysis
          </Link>
        </nav>
      </div>
    </header>
  );
}
