import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "KI Agentic Qualification System",
  description:
    "Agentic startup qualification platform — Phase 1 EVAL & TEAM assessment powered by Claude.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body suppressHydrationWarning className="min-h-screen bg-gray-50 text-slate-900">
        <nav className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <a href="/" className="text-xl font-bold text-brand-600 tracking-tight">
            KI Agentic
          </a>
          <div className="flex items-center gap-6 text-sm font-medium text-gray-600">
            <a href="/dashboard" className="hover:text-brand-600 transition-colors">
              Dashboard
            </a>
            <a
              href="/submit"
              className="bg-brand-500 text-white px-4 py-2 rounded-lg hover:bg-brand-600 transition-colors"
            >
              Submit Startup
            </a>
          </div>
        </nav>
        <main className="max-w-5xl mx-auto px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
