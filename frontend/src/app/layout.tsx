import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Florida Man Bioscience — Peptide-led precision therapeutics",
    template: "%s · Florida Man Bioscience",
  },
  description:
    "Florida Man Bioscience builds peptide-led precision medicine: genome-aware response prediction, longitudinal biomarker tracking, and a delivery platform for next-generation therapeutics.",
  metadataBase: new URL("https://flmanbiosci.net"),
  openGraph: {
    type: "website",
    siteName: "Florida Man Bioscience",
    url: "https://flmanbiosci.net/",
    title: "Florida Man Bioscience — Peptide-led precision therapeutics",
    description:
      "Genome-aware peptide response prediction, longitudinal biomarker tracking, and a delivery platform for next-generation therapeutics.",
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
