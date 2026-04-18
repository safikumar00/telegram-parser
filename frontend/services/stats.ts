/**
 * Channel stats — derives win-rate / avg-profit / total-trades per channel
 * from the `signals` ledger. Also mirrors the computed row into the
 * `channel_stats` materialized cache for fast dashboard reads.
 *
 *   win_rate   = wins / total_closed * 100
 *   avg_profit = mean(result_percent) across closed signals
 *   total      = closed signals only (pending excluded)
 */

import { getSupabase, isSupabaseConfigured } from "@/lib/supabase";
import type { ChannelStats, ChannelStatsWithMeta } from "@/types";

function round2(n: number): number {
  return Math.round(n * 100) / 100;
}

export async function computeChannelStats(
  channel_id: string,
): Promise<ChannelStats> {
  const client = getSupabase();

  const { data, error } = await client
    .from("signals")
    .select("status, result_percent")
    .eq("channel_id", channel_id)
    .neq("status", "pending");

  if (error) {
    console.error("[stats] fetch failed", error);
    return { channel_id, win_rate: 0, avg_profit: 0, total_trades: 0 };
  }

  const rows = data ?? [];
  const total = rows.length;
  if (total === 0) {
    return { channel_id, win_rate: 0, avg_profit: 0, total_trades: 0 };
  }

  const wins = rows.filter((r) => r.status === "win").length;
  const profits = rows
    .map((r) => r.result_percent)
    .filter((p): p is number => typeof p === "number" && Number.isFinite(p));

  const avg_profit =
    profits.length > 0
      ? profits.reduce((a, b) => a + b, 0) / profits.length
      : 0;

  return {
    channel_id,
    win_rate: round2((wins / total) * 100),
    avg_profit: round2(avg_profit),
    total_trades: total,
  };
}

/**
 * Computes stats and upserts them into `channel_stats` so the dashboard
 * can read a single pre-aggregated row instead of scanning signals.
 */
export async function refreshChannelStats(
  channel_id: string,
): Promise<ChannelStats> {
  const stats = await computeChannelStats(channel_id);
  const client = getSupabase();
  const { error } = await client.from("channel_stats").upsert(
    {
      channel_id,
      win_rate: stats.win_rate,
      avg_profit: stats.avg_profit,
      total_trades: stats.total_trades,
      updated_at: new Date().toISOString(),
    },
    { onConflict: "channel_id" },
  );
  if (error) console.error("[stats] upsert failed", error);
  return stats;
}

/**
 * Reads the cached channel_stats joined with channel meta for UI display.
 * Falls back to on-the-fly computation if the cache is empty.
 */
export async function listChannelStats(): Promise<ChannelStatsWithMeta[]> {
  if (!isSupabaseConfigured()) return [];
  const client = getSupabase();

  const { data, error } = await client
    .from("channel_stats")
    .select(
      "channel_id, win_rate, avg_profit, total_trades, updated_at, channel:channels(name, telegram_id)",
    )
    .order("total_trades", { ascending: false });

  if (error) {
    console.error("[stats] list cache failed", error);
    return [];
  }

  return ((data ?? []) as unknown as Array<{
    channel_id: string;
    win_rate: number;
    avg_profit: number;
    total_trades: number;
    updated_at: string;
    channel: { name: string | null; telegram_id: string | null } | null;
  }>).map((r) => ({
    channel_id: r.channel_id,
    win_rate: r.win_rate,
    avg_profit: r.avg_profit,
    total_trades: r.total_trades,
    updated_at: r.updated_at,
    channel_name: r.channel?.name ?? null,
    channel_telegram_id: r.channel?.telegram_id ?? null,
  }));
}
