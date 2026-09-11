import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Florida Man Bioscience — Peptide options, matched to the genome",
    template: "%s · Florida Man Bioscience",
  },
  description:
    "Florida Man Bioscience builds PeptOdyssey — genome-informed peptide options a licensed clinician can review, plus Stage A design software and research-stage delivery.",
  metadataBase: new URL("https://flmanbiosci.net"),
  openGraph: {
    type: "website",
    siteName: "Florida Man Bioscience",
    url: "https://flmanbiosci.net/",
    title: "Florida Man Bioscience — Peptide options, matched to the genome",
    description:
      "Genome-informed peptide options a licensed clinician can review. Design is Stage A. Delivery stays research.",
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
