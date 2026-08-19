import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Florida Man Bioscience — Peptide medicine, matched to the genome",
    template: "%s · Florida Man Bioscience",
  },
  description:
    "Florida Man Bioscience builds PeptOdyssey — genome-aware peptide decision support, a clinician-readable dossier, biomarker tracking, and research-stage delivery science.",
  metadataBase: new URL("https://flmanbiosci.net"),
  openGraph: {
    type: "website",
    siteName: "Florida Man Bioscience",
    url: "https://flmanbiosci.net/",
    title: "Florida Man Bioscience — Peptide medicine, matched to the genome",
    description:
      "Genome-aware peptide decision support, longitudinal biomarker tracking, and research-stage delivery science.",
    images: [{ url: "/assets/img/mark.png" }],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen bg-[#f5f4f0] text-[#0d1117]">
        {children}
      </body>
    </html>
  );
}
