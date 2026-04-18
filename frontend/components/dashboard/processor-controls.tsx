"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { RefreshCcw, Zap } from "lucide-react";

interface CronState {
  status: "idle" | "running" | "ok" | "error";
  message: string | null;
}

export function ProcessorControls() {
  const router = useRouter();
  const [isPending, start] = useTransition();
  const [cron, setCron] = useState<CronState>({
    status: "idle",
    message: null,
  });

  async function runCron() {
    setCron({ status: "running", message: "Contacting processor…" });
    try {
      const res = await fetch("/api/cron/process", { method: "POST" });
      const body = await res.json();
      if (!res.ok || !body.ok) {
        setCron({
          status: "error",
          message: body.error ?? `HTTP ${res.status}`,
        });
        return;
      }
      setCron({
        status: "ok",
        message: `scanned ${body.scanned} · updated ${body.updated} · skipped ${body.skipped} · ${body.durationMs}ms`,
      });
      start(() => router.refresh());
    } catch (err) {
      setCron({ status: "error", message: (err as Error).message });
    }
  }

  return (
    <div
      data-testid="processor-controls"
      className="flex flex-wrap items-center gap-3"
    >
      <Button
        size="sm"
        variant="outline"
        onClick={() => start(() => router.refresh())}
        data-testid="dashboard-refresh-button"
        disabled={isPending}
      >
        <RefreshCcw
          className={`mr-1.5 h-3.5 w-3.5 ${isPending ? "animate-spin" : ""}`}
          strokeWidth={2}
        />
        Refresh
      </Button>
      <Button
        size="sm"
        onClick={runCron}
        data-testid="run-cron-button"
        disabled={cron.status === "running"}
      >
        <Zap className="mr-1.5 h-3.5 w-3.5" strokeWidth={2} />
        {cron.status === "running" ? "Running…" : "Run processor now"}
      </Button>
      {cron.message && (
        <Badge
          data-testid="cron-feedback"
          variant={
            cron.status === "error"
              ? "destructive"
              : cron.status === "ok"
              ? "success"
              : "secondary"
          }
          className="rounded-full font-mono text-[10px] uppercase tracking-wider"
        >
          {cron.message}
        </Badge>
      )}
    </div>
  );
}
