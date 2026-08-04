"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const PRODUCT_PREFIXES = [
  "/peptodyssey",
  "/jobs",
  "/tracking",
  "/regulatory",
  "/study",
  "/faq",
];

function isProductPath(pathname: string | null): boolean {
  if (!pathname) return false;
  if (pathname === "/") return false;
  return PRODUCT_PREFIXES.some(
    (p) => pathname === p || pathname.startsWith(`${p}/`)
  );
}

export function Nav() {
  const pathname = usePathname();
  const product = isProductPath(pathname);
  const [open, setOpen] = useState(false);

  if (product) {
    return (
      <header className="relative border-b border-[#1a6b4a]/30 bg-[#0d1117]">
        <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4">
          <div className="flex items-center gap-4">
            <Link
              href="/peptodyssey"
              className="flex items-center gap-2.5 transition-opacity hover:opacity-90"
            >
              <span className="text-lg text-[#2d8f61]">&#x2726;</span>
              <span
                className="text-lg tracking-tight text-white"
                style={{ fontFamily: "'DM Serif Display', serif" }}
              >
                PeptOdyssey
              </span>
            </Link>
            <Link
              href="/"
              className="hidden text-xs font-medium text-zinc-500 transition-colors hover:text-zinc-300 sm:inline"
            >
              FMB ↗
            </Link>
          </div>

          <button
            type="button"
            className="rounded-md p-2 text-zinc-300 sm:hidden"
            aria-expanded={open}
            aria-label="Toggle navigation"
            onClick={() => setOpen((v) => !v)}
          >
            <span className="block text-lg leading-none">{open ? "×" : "☰"}</span>
          </button>

          <nav
            className={`${
              open
                ? "absolute left-0 right-0 top-14 z-40 flex flex-col gap-1 border-b border-[#1a6b4a]/30 bg-[#0d1117] px-4 py-3"
                : "hidden"
            } sm:static sm:flex sm:flex-row sm:items-center sm:gap-5 sm:border-0 sm:bg-transparent sm:p-0 text-sm`}
          >
            <Link
              href="/peptodyssey"
              className="py-1.5 text-zinc-400 transition-colors hover:text-white"
              onClick={() => setOpen(false)}
            >
              Hub
            </Link>
            <Link
              href="/peptodyssey/analyze"
              className="py-1.5 text-zinc-400 transition-colors hover:text-white"
              onClick={() => setOpen(false)}
            >
              Analyze
            </Link>
            <Link
              href="/jobs"
              className="py-1.5 text-zinc-400 transition-colors hover:text-white"
              onClick={() => setOpen(false)}
            >
              History
            </Link>
            <Link
              href="/tracking"
              className="py-1.5 text-zinc-400 transition-colors hover:text-white"
              onClick={() => setOpen(false)}
            >
              Tracking
            </Link>
            <Link
              href="/regulatory"
              className="py-1.5 text-zinc-400 transition-colors hover:text-white"
              onClick={() => setOpen(false)}
            >
              Regulatory
            </Link>
            <Link
              href="/study"
              className="py-1.5 text-zinc-400 transition-colors hover:text-white"
              onClick={() => setOpen(false)}
            >
              Study
            </Link>
            <Link
              href="/peptodyssey/privacy"
              className="py-1.5 text-zinc-400 transition-colors hover:text-white"
              onClick={() => setOpen(false)}
            >
              Privacy
            </Link>
          </nav>
        </div>
      </header>
    );
  }

  return (
    <header className="sticky top-0 z-50 border-b border-[#edecea] bg-white/90 backdrop-blur">
      <div className="relative mx-auto flex h-14 max-w-5xl items-center justify-between px-4">
        <Link
          href="/"
          className="flex items-center gap-2.5 transition-opacity hover:opacity-90"
        >
          <span
            className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-[#1a6b4a] to-[#0f4530] text-sm text-white"
            style={{ fontFamily: "'DM Serif Display', serif" }}
            aria-hidden
          >
            F
          </span>
          <span
            className="text-lg tracking-tight text-[#0d1117]"
            style={{ fontFamily: "'DM Serif Display', serif" }}
          >
            Florida Man Bioscience
          </span>
        </Link>

        <button
          type="button"
          className="rounded-md p-2 text-[#0d1117] sm:hidden"
          aria-expanded={open}
          aria-label="Toggle navigation"
          onClick={() => setOpen((v) => !v)}
        >
          <span className="block text-lg leading-none">{open ? "×" : "☰"}</span>
        </button>

        <nav
          className={`${
            open
              ? "absolute left-0 right-0 top-14 z-40 flex flex-col gap-1 border-b border-[#edecea] bg-white px-4 py-3 shadow-sm"
              : "hidden"
          } sm:static sm:flex sm:flex-row sm:items-center sm:gap-6 sm:border-0 sm:bg-transparent sm:p-0 sm:shadow-none text-sm`}
        >
          <a
            href="/#philosophy"
            className="py-1.5 font-medium text-[#3a3f4a] transition-colors hover:text-[#1a6b4a]"
            onClick={() => setOpen(false)}
          >
            Philosophy
          </a>
          <a
            href="/#products"
            className="py-1.5 font-medium text-[#3a3f4a] transition-colors hover:text-[#1a6b4a]"
            onClick={() => setOpen(false)}
          >
            Products
          </a>
          <a
            href="/#contact"
            className="py-1.5 font-medium text-[#3a3f4a] transition-colors hover:text-[#1a6b4a]"
            onClick={() => setOpen(false)}
          >
            Contact
          </a>
          <Link
            href="/peptodyssey"
            className="inline-flex items-center justify-center rounded-full bg-[#0d1117] px-4 py-2 text-xs font-semibold text-white transition-colors hover:bg-[#1a6b4a]"
            onClick={() => setOpen(false)}
          >
            PeptOdyssey →
          </Link>
        </nav>
      </div>
    </header>
  );
}
