export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <main className="min-h-screen bg-canvas px-4 py-10 md:px-6 md:py-20">
      <div className="mx-auto max-w-6xl">{children}</div>
    </main>
  );
}
