import type { Metadata } from "next";
import "./globals.css";
import { Nav } from "./components/Nav";

export const metadata: Metadata = {
  title: {
    default: "Florida Man Bioscience — Peptide medicine, matched to the genome",
    template: "%s · Florida Man Bioscience",
  },
  description:
    "Florida Man Bioscience builds the analytics, trackers, and delivery research platform behind precision peptide therapy.",
  metadataBase: new URL("https://flmanbiosci.net"),
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen bg-[#f5f4f0]">
        <Nav />
        <main className="mx-auto max-w-5xl px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
