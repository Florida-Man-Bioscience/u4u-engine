import { Nav } from "@/app/components/Nav";

export default function ProductLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <>
      <Nav />
      <main className="mx-auto max-w-5xl px-4 py-8">{children}</main>
    </>
  );
}
