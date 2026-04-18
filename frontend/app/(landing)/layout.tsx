import Link from "next/link";
import { cn } from "@/lib/utils";

export default function LandingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative min-h-screen overflow-x-hidden bg-[#F6F6F4] text-foreground">
      {/* Ambient glow */}
      <div className="pointer-events-none absolute inset-x-0 top-0 h-[720px] radial-glow" />
      <div
        className={cn(
          "pointer-events-none absolute inset-0 grain opacity-30",
        )}
      />

      <header className="relative z-10 mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-6">
        <Link
          href="/"
          data-testid="brand-home-link"
          className="flex items-center gap-2"
        >
          <LogoMark />
          <span className="text-base font-semibold tracking-tight">
            SignalOS
          </span>
          <span className="ml-2 rounded-full border border-border/60 bg-white/60 px-2 py-0.5 text-[10px] font-medium uppercase tracking-widest text-muted-foreground backdrop-blur">
            Phase 1
          </span>
        </Link>

        <nav className="hidden items-center gap-8 text-sm text-muted-foreground md:flex">
          <a
            href="#features"
            data-testid="nav-features-link"
            className="transition-colors hover:text-foreground"
          >
            Features
          </a>
          <a
            href="#pipeline"
            data-testid="nav-pipeline-link"
            className="transition-colors hover:text-foreground"
          >
            Pipeline
          </a>
          <Link
            href="/dashboard"
            data-testid="nav-dashboard-link"
            className="transition-colors hover:text-foreground"
          >
            Dashboard
          </Link>
        </nav>

        <Link
          href="/dashboard"
          data-testid="header-cta-link"
          className="inline-flex h-9 items-center rounded-full bg-foreground px-4 text-xs font-medium text-background transition-transform hover:-translate-y-px"
        >
          Open dashboard
        </Link>
      </header>

      <main className="relative z-10">{children}</main>

      <footer className="relative z-10 border-t border-border/50 bg-white/40 backdrop-blur">
        <div className="mx-auto flex w-full max-w-6xl flex-col items-start justify-between gap-4 px-6 py-8 text-sm text-muted-foreground md:flex-row md:items-center">
          <div className="flex items-center gap-2">
            <LogoMark className="h-4 w-4" />
            <span>© {new Date().getFullYear()} SignalOS — Ingest. Parse. Audit.</span>
          </div>
          <div className="flex items-center gap-6">
            <span className="font-mono text-xs">v0.1 · ingestion</span>
            <Link
              href="/dashboard"
              data-testid="footer-dashboard-link"
              className="hover:text-foreground"
            >
              Dashboard →
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}

function LogoMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 32 32"
      className={cn("h-5 w-5", className)}
      aria-hidden="true"
    >
      <rect width="32" height="32" rx="9" fill="#0A0B14" />
      <path
        d="M9 21 L14 16 L17.5 19 L23 11"
        stroke="url(#g)"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      <circle cx="23" cy="11" r="1.75" fill="#A78BFA" />
      <defs>
        <linearGradient id="g" x1="9" y1="21" x2="23" y2="11">
          <stop stopColor="#60A5FA" />
          <stop offset="1" stopColor="#A78BFA" />
        </linearGradient>
      </defs>
    </svg>
  );
}
