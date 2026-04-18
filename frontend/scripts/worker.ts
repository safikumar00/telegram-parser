/**
 * Local / self-hosted interval worker.
 *
 * Alternative to Vercel Cron — runs `processSignals()` every N minutes
 * inside a long-lived Node process.
 *
 * Usage:
 *   TELEGRAM_BOT_TOKEN=... NEXT_PUBLIC_SUPABASE_URL=... \
 *   NEXT_PUBLIC_SUPABASE_ANON_KEY=... \
 *   yarn worker
 *
 * For Next.js-integrated environments prefer the `/api/cron/process`
 * route hit by Vercel Cron or an external scheduler.
 */

import { processSignals } from "@/services/processor";

const INTERVAL_MS = Number(process.env.PROCESSOR_INTERVAL_MS ?? 3 * 60_000);

async function tick() {
  try {
    const res = await processSignals();
    console.log(
      `[worker] tick ok · scanned=${res.scanned} updated=${res.updated} skipped=${res.skipped} errors=${res.errors} in ${res.durationMs}ms`,
    );
  } catch (err) {
    console.error("[worker] tick failed", err);
  }
}

console.log(`[worker] boot · interval=${INTERVAL_MS}ms`);
void tick();
setInterval(tick, INTERVAL_MS);
