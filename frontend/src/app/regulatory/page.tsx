export const metadata = {
  title: "FDA Peptide Regulatory Dashboard",
};

export default function RegulatoryDashboardPage() {
  return (
    <div className="relative left-1/2 right-1/2 -mx-[50vw] w-screen -my-8 h-[calc(100vh-3.5rem)]">
      <iframe
        src="/regulatory-dashboard.html"
        title="FDA Peptide Regulatory Dashboard"
        className="w-full h-full border-0 block"
      />
    </div>
  );
}
