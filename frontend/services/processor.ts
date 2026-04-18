/**
 * Signal processor — the cron-driven evaluator.
 *
 *   1. Pull pending signals (bounded page size so cron never starves).
 *   2. For each, fetch current price.
 *   3. Evaluate. Only write if status transitioned away from 'pending'.
 *   4. Atomic-ish guard: the UPDATE matches `status='pending'` so concurrent
 *      runs never double-close the same row.
 *   5. After batch → refresh channel_stats for every touched channel.
 */

import { getSupabase, isSupabaseConfigured } from "@/lib/supabase";
import { getCurrentPrice } from "@/services/prices";
import { evaluateSignal } from "@/services/evaluator";
import { refreshChannelStats } from "@/services/stats";
import type { Signal } from "@/types";

const DEFAULT_PAGE = 200;

export interface ProcessorResult {
  scanned: number;
  updated: number;
  skipped: number;
  errors: number;
  touchedChannels: string[];
  durationMs: number;
}

export async function processSignals(
  opts: { limit?: number } = {},
): Promise<ProcessorResult> {
  const started = Date.now();
  const limit = opts.limit ?? DEFAULT_PAGE;

  const result: ProcessorResult = {
    scanned: 0,
    updated: 0,
    skipped: 0,
    errors: 0,
    touchedChannels: [],
    durationMs: 0,
  };

  if (!isSupabaseConfigured()) {
    console.warn("[processor] Supabase not configured — skipping run");
    result.durationMs = Date.now() - started;
    return result;
  }

  const client = getSupabase();

  const { data: pending, error } = await client
    .from("signals")
    .select("*")
    .eq("status", "pending")
    .order("created_at", { ascending: true })
    .limit(limit);

  if (error) {
    console.error("[processor] fetch pending failed", error);
    result.errors += 1;
    result.durationMs = Date.now() - started;
    return result;
  }

  const signals = (pending ?? []) as Signal[];
  result.scanned = signals.length;
  console.log(`[processor] scanned ${signals.length} pending signal(s)`);

  const touched = new Set<string>();

  for (const s of signals) {
    console.log(`[processor] Processing signal ${s.id} (${s.pair})`);

    if (!s.pair) {
      console.log(`[processor] skip ${s.id}: no pair`);
      result.skipped += 1;
      continue;
    }

    const price = await getCurrentPrice(s.pair);
    console.log(`[processor] Fetched price for ${s.pair}:`, price);
    if (price === null) {
      result.skipped += 1;
      continue;
    }

    const decision = evaluateSignal(
      {
        entry: s.entry,
        stop_loss: s.stop_loss,
        take_profit: s.take_profit,
        status: s.status,
      },
      price,
    );
    console.log(`[processor] Evaluation result for ${s.id}:`, decision);

    if (decision.status === "pending") {
      result.skipped += 1;
      continue;
    }

    // Guarded update: only transition rows that are still `pending`.
    const { data: updated, error: upErr } = await client
      .from("signals")
      .update({
        status: decision.status,
        result_percent: decision.result_percent,
        closed_at: decision.closed_at?.toISOString() ?? null,
      })
      .eq("id", s.id)
      .eq("status", "pending")
      .select()
      .maybeSingle();

    console.log(`[processor] DB update result for ${s.id}:`, {
      ok: Boolean(updated),
      error: upErr?.message,
    });

    if (upErr) {
      result.errors += 1;
      continue;
    }
    if (updated) {
      result.updated += 1;
      if (s.channel_id) touched.add(s.channel_id);
    } else {
      // Row was already closed by a concurrent run — not an error.
      result.skipped += 1;
    }
  }

  // Refresh stats for every channel that saw a transition.
  for (const channelId of touched) {
    try {
      await refreshChannelStats(channelId);
    } catch (e) {
      console.error("[processor] stats refresh failed", channelId, e);
      result.errors += 1;
    }
  }

  result.touchedChannels = Array.from(touched);
  result.durationMs = Date.now() - started;
  console.log("[processor] run complete", result);
  return result;
}
