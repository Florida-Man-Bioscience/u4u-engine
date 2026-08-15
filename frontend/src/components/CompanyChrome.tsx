import type { ReactNode } from "react";
import Link from "next/link";

const serif = { fontFamily: "'DM Serif Display', serif" } as const;

type Props = {
  /** Active nav key */
  active?: "home" | "team" | "peptodyssey" | "products";
  children: ReactNode;
};

/** Shared marketing chrome for company pages (home, /team, products …). */
export function CompanyChrome({ active = "home", children }: Props) {
  const link = (key: Props["active"], href: string, label: string) => {
    const isActive = active === key;
    return (
      <Link
        href={href}
        className={
          isActive
            ? "text-[#1a6b4a]"
            : "text-[#3a3f4a] hover:text-[#1a6b4a]"
        }
        aria-current={isActive ? "page" : undefined}
      >
        {label}
      </Link>
    );
  };

  return (
    <div className="bg-white text-[#0d1117]">
      <header className="sticky top-0 z-50 border-b border-[#edecea] bg-white/85 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-[1180px] items-center justify-between px-6 md:px-7">
          <Link href="/" className="flex items-center gap-2.5">
            <span
              className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-[#1a6b4a] to-[#0f4530] text-sm text-white"
              style={serif}
              aria-hidden
            >
              F
            </span>
            <span
              className="text-lg tracking-tight text-[#0d1117]"
              style={serif}
            >
              Florida Man Bioscience
            </span>
          </Link>
          <nav className="hidden items-center gap-7 text-sm font-medium sm:flex">
            {link("home", "/#philosophy", "Philosophy")}
            {link("home", "/#platform", "Platform")}
            {link("products", "/#products", "Programs")}
            {link("team", "/team", "Team")}
            <Link
              href="/products/u4u"
              className="text-[#3a3f4a] hover:text-[#1a6b4a]"
            >
              U4U
            </Link>
            <Link
              href="/peptodyssey"
              className="rounded-full bg-[#1a6b4a] px-4 py-2 text-white hover:bg-[#0f4530]"
            >
              PeptOdyssey
            </Link>
          </nav>
          <Link
            href="/peptodyssey"
            className="rounded-full bg-[#1a6b4a] px-3 py-1.5 text-sm font-medium text-white sm:hidden"
          >
            Product
          </Link>
        </div>
      </header>
      {children}
      <footer className="border-t border-[#edecea] bg-[#f5f4f0] py-10">
        <div className="mx-auto flex max-w-[1180px] flex-col gap-4 px-6 text-sm text-[#6b7280] md:flex-row md:items-center md:justify-between md:px-7">
          <div>
            <span className="font-semibold text-[#0d1117]">
              Florida Man Bioscience
            </span>
            <span className="mx-2">·</span>
            Detect → Design → Deliver
          </div>
          <div className="flex flex-wrap gap-4">
            <Link href="/#products" className="hover:text-[#1a6b4a]">
              Programs
            </Link>
            <Link href="/products/u4u" className="hover:text-[#1a6b4a]">
              U4U
            </Link>
            <Link href="/team" className="hover:text-[#1a6b4a]">
              Team
            </Link>
            <Link href="/peptodyssey" className="hover:text-[#1a6b4a]">
              PeptOdyssey
            </Link>
            <a
              href="https://github.com/Florida-Man-Bioscience"
              className="hover:text-[#1a6b4a]"
              rel="noopener noreferrer"
            >
              GitHub
            </a>
            <a
              href="mailto:hello@flmanbiosci.net"
              className="hover:text-[#1a6b4a]"
            >
              hello@flmanbiosci.net
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}

export { serif as companySerif };
