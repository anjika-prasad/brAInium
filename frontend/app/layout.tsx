import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Unified Asset & Operations Brain",
  description: "Industrial Knowledge Intelligence platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="blueprint-bg min-h-screen">
        <header className="border-b border-blueprint-line/40 bg-blueprint-950/80 backdrop-blur sticky top-0 z-20">
          <div className="mx-auto max-w-6xl px-6 py-4 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-3">
              <span className="font-mono text-amber-signal text-xs border border-amber-signal/60 rounded px-1.5 py-0.5">
                IKB-01
              </span>
              <span className="font-display font-semibold text-lg tracking-tight text-paper">
                Unified Asset &amp; Operations Brain
              </span>
            </Link>
            <nav className="flex gap-6 font-mono text-sm text-paper/70">
              <Link href="/" className="hover:text-amber-signal transition-colors">
                Copilot
              </Link>
              <Link href="/upload" className="hover:text-amber-signal transition-colors">
                Ingest
              </Link>
              <Link href="/graph" className="hover:text-amber-signal transition-colors">
                Knowledge Graph
              </Link>
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-6xl px-6 py-10">{children}</main>
      </body>
    </html>
  );
}
