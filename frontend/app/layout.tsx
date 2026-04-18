import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SignalOS — Signal Ingestion for Serious Traders",
  description:
    "Structured, audit-ready Telegram signal intelligence. Ingest, parse, and store trading signals at operator-grade quality.",
  icons: {
    icon: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='24' fill='%230A0B14'/%3E%3Cpath d='M30 65 L45 50 L55 58 L70 35' stroke='%238B9AFF' stroke-width='6' stroke-linecap='round' stroke-linejoin='round' fill='none'/%3E%3Ccircle cx='70' cy='35' r='5' fill='%238B9AFF'/%3E%3C/svg%3E",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap"
        />
      </head>
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
