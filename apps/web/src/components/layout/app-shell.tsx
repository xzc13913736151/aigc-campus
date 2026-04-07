import { Navbar } from "@/components/layout/navbar";


export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-canvas">
      <Navbar />
      <main className="mx-auto max-w-6xl px-4 py-10 md:px-6">{children}</main>
    </div>
  );
}
