import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SignalsTable } from "@/components/dashboard/signals-table";
import { ParserPlayground } from "@/components/dashboard/parser-playground";
import { listSignals } from "@/services/signals";
import { isSupabaseConfigured } from "@/lib/supabase";
import { Activity, Radio, Terminal, type LucideIcon } from "lucide-react";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const configured = isSupabaseConfigured();
  const signals = configured ? await safeList() : [];
  const channels = new Set(
    signals.map((s) => s.channel?.telegram_id).filter(Boolean),
  );

  return (
    <div className="space-y-10">
      <section data-testid="dashboard-header">
        <div className="text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
          Signal ledger
        </div>
        <div className="mt-3 flex flex-col items-start justify-between gap-6 md:flex-row md:items-end">
          <h1 className="max-w-2xl text-4xl font-medium tracking-tight md:text-5xl">
            Every signal, every channel,{" "}
            <span
              className="italic text-gradient"
              style={{ fontFamily: "var(--font-display)" }}
            >
              structured.
            </span>
          </h1>
          <div className="flex flex-wrap items-center gap-2">
            {configured ? (
              <Badge
                variant="success"
                data-testid="supabase-status-badge"
                className="rounded-full"
              >
                Supabase connected
              </Badge>
            ) : (
              <Badge
                variant="warning"
                data-testid="supabase-status-badge"
                className="rounded-full"
              >
                Supabase not configured
              </Badge>
            )}
            <Badge
              variant="outline"
              data-testid="env-mode-badge"
              className="rounded-full border-border/70 bg-white/60"
            >
              {process.env.NODE_ENV}
            </Badge>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-5 md:grid-cols-3">
        <StatCard
          icon={Activity}
          label="Signals ingested"
          value={signals.length}
          testid="stat-signals"
        />
        <StatCard
          icon={Radio}
          label="Active channels"
          value={channels.size}
          testid="stat-channels"
        />
        <StatCard
          icon={Terminal}
          label="Pipeline"
          value="Telegraf → Parser → Supabase"
          testid="stat-pipeline"
          mono
        />
      </section>

      <section className="grid grid-cols-1 gap-8 xl:grid-cols-[1.6fr_1fr]">
        <Card data-testid="signals-card" className="overflow-hidden">
          <CardHeader className="flex flex-row items-center justify-between gap-4 border-b border-border/50 pb-5">
            <div>
              <CardTitle className="text-lg">Recent signals</CardTitle>
              <p className="mt-1 text-sm text-muted-foreground">
                Last 100 ingested broadcasts, newest first.
              </p>
            </div>
            <Badge
              variant="outline"
              className="rounded-full border-border/70 bg-white/70 font-mono text-[10px] uppercase tracking-[0.18em]"
            >
              live
            </Badge>
          </CardHeader>
          <CardContent className="p-0">
            {!configured ? (
              <EmptyState
                title="Supabase is not configured yet"
                body="Add NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY to .env.local, then run the schema from the README."
                testid="supabase-empty-state"
              />
            ) : signals.length === 0 ? (
              <EmptyState
                title="Waiting for your first signal"
                body="Point your Telegram bot at /api/telegram — the first valid signal will appear here instantly."
                testid="signals-empty-state"
              />
            ) : (
              <SignalsTable signals={signals} />
            )}
          </CardContent>
        </Card>

        <ParserPlayground />
      </section>
    </div>
  );
}

async function safeList() {
  try {
    return await listSignals(100);
  } catch (err) {
    console.error("[dashboard] listSignals failed", err);
    return [];
  }
}

function StatCard({
  icon: Icon,
  label,
  value,
  testid,
  mono,
}: {
  icon: LucideIcon;
  label: string;
  value: string | number;
  testid: string;
  mono?: boolean;
}) {
  return (
    <Card data-testid={testid} className="relative overflow-hidden">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-border/70 bg-white/80 text-indigo-500">
            <Icon className="h-4 w-4" strokeWidth={1.75} />
          </div>
          <span className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
            {label}
          </span>
        </div>
      </CardHeader>
      <CardContent>
        <div
          className={`text-2xl tracking-tight ${
            mono ? "font-mono text-base" : "font-medium"
          }`}
        >
          {value}
        </div>
      </CardContent>
    </Card>
  );
}

function EmptyState({
  title,
  body,
  testid,
}: {
  title: string;
  body: string;
  testid: string;
}) {
  return (
    <div
      data-testid={testid}
      className="flex flex-col items-start gap-3 p-10 text-sm"
    >
      <div className="text-base font-medium text-foreground">{title}</div>
      <div className="max-w-xl leading-relaxed text-muted-foreground">
        {body}
      </div>
    </div>
  );
}
