import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ArrowRight, Cable, Gauge, ScanSearch, Waypoints } from "lucide-react";

export default function LandingPage() {
  return (
    <>
      <Hero />
      <TerminalPreview />
      <Features />
      <Pipeline />
      <CTA />
    </>
  );
}

function Hero() {
  return (
    <section className="relative mx-auto w-full max-w-6xl px-6 pt-20 pb-28 md:pt-28 md:pb-36">
      <div className="animate-fade-up">
        <Badge
          variant="outline"
          data-testid="hero-status-badge"
          className="mb-8 border-border/70 bg-white/70 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.2em] text-muted-foreground backdrop-blur"
        >
          <span className="relative mr-2 inline-flex h-1.5 w-1.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-500" />
          </span>
          Ingestion pipeline live
        </Badge>
      </div>

      <h1
        data-testid="hero-heading"
        className="max-w-4xl animate-fade-up text-5xl font-medium leading-[1.02] tracking-tight text-foreground md:text-6xl lg:text-7xl"
        style={{ animationDelay: "80ms" }}
      >
        The signal layer for{" "}
        <span
          className="font-[450] italic text-gradient"
          style={{ fontFamily: "var(--font-display)" }}
        >
          serious traders.
        </span>
      </h1>

      <p
        className="mt-8 max-w-2xl animate-fade-up text-lg leading-relaxed text-muted-foreground md:text-xl"
        style={{ animationDelay: "160ms" }}
      >
        SignalOS ingests raw Telegram broadcasts, parses them into structured
        trades, and stores every pair, entry, stop and target — so your desk can
        finally audit, replay and trust what it trades on.
      </p>

      <div
        className="mt-10 flex animate-fade-up flex-col items-start gap-3 sm:flex-row sm:items-center"
        style={{ animationDelay: "240ms" }}
      >
        <Button
          size="lg"
          asChild
          data-testid="hero-primary-cta"
          className="group"
        >
          <Link href="/dashboard">
            Open live dashboard
            <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-0.5" />
          </Link>
        </Button>
        <Button
          size="lg"
          variant="outline"
          asChild
          data-testid="hero-secondary-cta"
        >
          <a href="#pipeline">See how ingestion works</a>
        </Button>
        <span className="ml-1 hidden items-center gap-2 text-xs text-muted-foreground sm:flex">
          <span className="h-1 w-1 rounded-full bg-muted-foreground/60" />
          No AI. Deterministic regex.
        </span>
      </div>

      <StatStrip />
    </section>
  );
}

function StatStrip() {
  const stats = [
    { k: "Signals parsed", v: "deterministic", sub: "regex-first pipeline" },
    { k: "Channels", v: "multi-tenant", sub: "per-channel provenance" },
    { k: "Storage", v: "Supabase", sub: "Postgres-native" },
    { k: "Latency", v: "<200ms", sub: "webhook → row" },
  ];
  return (
    <div
      className="mt-20 grid animate-fade-up grid-cols-2 gap-x-10 gap-y-8 border-t border-border/50 pt-10 md:grid-cols-4"
      style={{ animationDelay: "360ms" }}
      data-testid="hero-stat-strip"
    >
      {stats.map((s) => (
        <div key={s.k}>
          <div className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
            {s.k}
          </div>
          <div className="mt-2 text-xl font-medium tracking-tight text-foreground">
            {s.v}
          </div>
          <div className="mt-1 text-xs text-muted-foreground">{s.sub}</div>
        </div>
      ))}
    </div>
  );
}

function TerminalPreview() {
  return (
    <section className="relative mx-auto w-full max-w-6xl px-6 pb-28">
      <div
        data-testid="terminal-preview"
        className="relative overflow-hidden rounded-[28px] border border-border/60 bg-[#0B0C18] shadow-[0_30px_80px_-30px_rgba(40,40,90,0.4)]"
      >
        <div className="flex items-center justify-between border-b border-white/10 px-5 py-3">
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-[#FF5F57]" />
            <span className="h-2.5 w-2.5 rounded-full bg-[#FEBC2E]" />
            <span className="h-2.5 w-2.5 rounded-full bg-[#28C840]" />
          </div>
          <div className="font-mono text-[11px] text-white/40">
            signal-os/logs ▸ ingestion.ts
          </div>
          <div className="w-10" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-[1.1fr_1fr]">
          <div className="border-b border-white/10 p-6 md:border-b-0 md:border-r">
            <div className="font-mono text-xs leading-relaxed text-white/80">
              <div className="text-white/40">// Incoming message</div>
              <div>
                <span className="text-[#FF8CC8]">const</span> msg ={" "}
                <span className="text-[#9EDBFF]">
                  {`"🔥 BTC/USDT LONG Entry: 62000 - 62500 SL: 61500 TP1: 63000 TP2: 64000"`}
                </span>
              </div>
              <div className="mt-4 text-white/40">// parseSignal(msg)</div>
              <div>
                <span className="text-[#FF8CC8]">const</span> parsed ={" "}
                <span className="text-[#F7D675]">parseSignal</span>(msg);
              </div>
              <div className="mt-4 text-white/40">// output</div>
              <div className="text-white/90">{`{`}</div>
              <div className="pl-4">
                pair:{" "}
                <span className="text-[#9EDBFF]">{'"BTCUSDT"'}</span>,
              </div>
              <div className="pl-4">
                entry: <span className="text-[#B8F2C7]">62000</span>,
              </div>
              <div className="pl-4">
                stop_loss: <span className="text-[#B8F2C7]">61500</span>,
              </div>
              <div className="pl-4">
                take_profit: <span className="text-[#B8F2C7]">64000</span>,
              </div>
              <div>{`}`}</div>
            </div>
          </div>

          <div className="p-6">
            <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-white/40">
              pipeline
            </div>
            <ol className="mt-4 space-y-4 font-mono text-xs text-white/80">
              {[
                "log ▸ Incoming message",
                "parse ▸ parseSignal(text)",
                "validate ▸ require pair + entry",
                "channel ▸ getOrCreateChannel(ctx)",
                "store ▸ signals.insert(...)",
                "log ▸ DB insert result",
              ].map((step, i) => (
                <li
                  key={step}
                  className="flex items-start gap-3"
                  data-testid={`pipeline-step-${i}`}
                >
                  <span className="mt-0.5 inline-flex h-5 w-5 flex-none items-center justify-center rounded-full border border-white/15 text-[10px] text-white/50">
                    {i + 1}
                  </span>
                  <span>{step}</span>
                </li>
              ))}
            </ol>

            <div className="mt-6 rounded-2xl border border-white/10 bg-white/[0.04] p-4 text-xs leading-relaxed text-white/70">
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-white/40">
                guarantees
              </div>
              <div className="mt-2">
                Idempotent channel upsert. Deterministic parser. Structured rows
                that survive fork-feed noise.
              </div>
            </div>
          </div>
        </div>

        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 -bottom-px h-px shimmer-border"
        />
      </div>
    </section>
  );
}

function Features() {
  const items = [
    {
      icon: ScanSearch,
      title: "Deterministic parser",
      body: "Regex-first pipeline that handles emojis, entry ranges, multi-TP and messy broker copy — no model drift, ever.",
    },
    {
      icon: Cable,
      title: "Telegram-native",
      body: "Telegraf bot with polling or webhook. Ingest from any channel, group or bot DM with a single env flip.",
    },
    {
      icon: Waypoints,
      title: "Channel provenance",
      body: "Every signal carries the channel it came from. Upsert-safe. Your audit trail stays clean under duplicates.",
    },
    {
      icon: Gauge,
      title: "Built for Phase 2",
      body: "Structured Postgres rows via Supabase. Ready for execution engines, analytics and replay on day one.",
    },
  ];
  return (
    <section
      id="features"
      className="mx-auto w-full max-w-6xl px-6 pb-28"
      data-testid="features-section"
    >
      <div className="mb-12 flex items-end justify-between gap-6">
        <div>
          <div className="text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
            ·01 Capabilities
          </div>
          <h2 className="mt-3 max-w-xl text-3xl font-medium tracking-tight md:text-4xl">
            Production ingestion, zero heuristics.
          </h2>
        </div>
        <p className="hidden max-w-sm text-sm text-muted-foreground md:block">
          Every layer is pinned: no AI, no fuzzy matching, no surprise cost.
          What goes in is what gets stored.
        </p>
      </div>

      <div className="grid gap-5 md:grid-cols-2">
        {items.map((item) => (
          <Card
            key={item.title}
            data-testid={`feature-card-${item.title.toLowerCase().replace(/\s+/g, "-")}`}
            className="group relative overflow-hidden transition-all duration-300 hover:-translate-y-0.5 hover:shadow-[0_20px_48px_-16px_rgba(60,60,140,0.18)]"
          >
            <div
              aria-hidden
              className="pointer-events-none absolute inset-x-0 top-0 h-px shimmer-border opacity-0 transition-opacity group-hover:opacity-100"
            />
            <CardHeader className="gap-4">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-border/70 bg-white/80 text-indigo-500 shadow-sm">
                <item.icon className="h-5 w-5" strokeWidth={1.75} />
              </div>
              <CardTitle className="text-lg font-medium">
                {item.title}
              </CardTitle>
              <CardDescription className="text-[15px] leading-relaxed text-muted-foreground">
                {item.body}
              </CardDescription>
            </CardHeader>
          </Card>
        ))}
      </div>
    </section>
  );
}

function Pipeline() {
  const steps = [
    {
      n: "01",
      t: "Telegram update",
      d: "Webhook hits /api/telegram and dispatches to Telegraf.",
    },
    {
      n: "02",
      t: "Parse + validate",
      d: "parseSignal() normalizes, extracts, and rejects invalid messages.",
    },
    {
      n: "03",
      t: "Resolve channel",
      d: "getOrCreateChannel() upserts on telegram_id, never duplicates.",
    },
    {
      n: "04",
      t: "Persist",
      d: "createSignal() writes a typed row to the signals table.",
    },
  ];
  return (
    <section
      id="pipeline"
      data-testid="pipeline-section"
      className="mx-auto w-full max-w-6xl px-6 pb-28"
    >
      <div className="rounded-[28px] border border-border/60 bg-white/60 p-8 backdrop-blur md:p-12">
        <div className="mb-10 flex items-end justify-between gap-6">
          <div>
            <div className="text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
              ·02 Pipeline
            </div>
            <h2 className="mt-3 max-w-xl text-3xl font-medium tracking-tight md:text-4xl">
              Four hops from chat to query-ready row.
            </h2>
          </div>
        </div>

        <ol className="grid gap-6 md:grid-cols-4">
          {steps.map((s) => (
            <li
              key={s.n}
              data-testid={`pipeline-step-card-${s.n}`}
              className="group relative"
            >
              <div className="flex items-baseline gap-3">
                <span className="font-mono text-xs text-muted-foreground">
                  {s.n}
                </span>
                <span className="h-px flex-1 bg-border/70" />
              </div>
              <div className="mt-4 text-lg font-medium tracking-tight">
                {s.t}
              </div>
              <div className="mt-2 text-sm leading-relaxed text-muted-foreground">
                {s.d}
              </div>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

function CTA() {
  return (
    <section
      data-testid="cta-section"
      className="mx-auto w-full max-w-6xl px-6 pb-32"
    >
      <div className="relative overflow-hidden rounded-[28px] bg-[#0A0B14] p-10 text-white md:p-16">
        <div
          aria-hidden
          className="pointer-events-none absolute -right-20 -top-20 h-[360px] w-[360px] rounded-full"
          style={{
            background:
              "radial-gradient(circle, rgba(167,139,250,0.35), transparent 60%)",
          }}
        />
        <div
          aria-hidden
          className="pointer-events-none absolute -left-10 -bottom-24 h-[340px] w-[340px] rounded-full"
          style={{
            background:
              "radial-gradient(circle, rgba(96,165,250,0.25), transparent 60%)",
          }}
        />
        <div className="relative max-w-2xl">
          <div className="text-[11px] uppercase tracking-[0.2em] text-white/50">
            Ready when you are
          </div>
          <h3
            className="mt-4 text-3xl font-medium leading-tight tracking-tight md:text-5xl"
            style={{ fontFamily: "var(--font-display)", fontStyle: "italic" }}
          >
            Let your signals earn their structure.
          </h3>
          <p className="mt-5 max-w-lg text-base text-white/70">
            Point your Telegram bot at SignalOS and watch raw chatter become a
            query-ready ledger. Phase 1 is ingestion — Phase 2 starts the day
            after.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Button
              size="lg"
              asChild
              data-testid="cta-primary-button"
              className="bg-white text-[#0A0B14] hover:bg-white/90"
            >
              <Link href="/dashboard">
                Open dashboard
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button
              size="lg"
              variant="ghost"
              asChild
              data-testid="cta-secondary-button"
              className="text-white hover:bg-white/10 hover:text-white"
            >
              <a href="#pipeline">Inspect the pipeline</a>
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}
