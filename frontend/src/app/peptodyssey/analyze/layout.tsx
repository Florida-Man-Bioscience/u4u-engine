import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Analyze genome",
  description:
    "Upload a genome file for peptide-oriented variant analysis on PeptOdyssey.",
};

export default function AnalyzeLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
