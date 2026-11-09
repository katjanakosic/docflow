import type { Metadata } from "next";
import { Schibsted_Grotesk } from "next/font/google";
import Link from "next/link";

import "./globals.css";
import { Providers } from "./providers";

const schibsted = Schibsted_Grotesk({ subsets: ["latin"], variable: "--font-schibsted" });

export const metadata: Metadata = {
  title: "DocFlow",
  description: "Supplier invoices and purchase orders for Alpenhandel AG",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={schibsted.variable}>
      <body className="min-h-screen antialiased">
        <header className="border-b border-rule bg-sheet">
          <div className="mx-auto flex max-w-6xl items-baseline gap-4 px-8 py-4">
            <Link href="/documents" className="text-lg font-bold tracking-tight">
              DocFlow
            </Link>
            <span className="text-sm text-muted">Supplier documents for Alpenhandel AG</span>
          </div>
        </header>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}