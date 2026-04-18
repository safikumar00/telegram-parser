import { getSupabase } from "@/lib/supabase";
import type { Signal, SignalWithChannel } from "@/types";

export interface CreateSignalInput {
  channel_id: string | null;
  pair: string;
  entry: number;
  stop_loss: number | null;
  take_profit: number | null;
  status?: string;
}

export async function createSignal(
  data: CreateSignalInput,
): Promise<Signal | null> {
  const client = getSupabase();
  const { data: row, error } = await client
    .from("signals")
    .insert({
      channel_id: data.channel_id,
      pair: data.pair,
      entry: data.entry,
      stop_loss: data.stop_loss,
      take_profit: data.take_profit,
      status: data.status ?? "pending",
    })
    .select()
    .single();

  if (error) {
    console.error("[signals] insert failed", error);
    return null;
  }
  return row as Signal;
}

export async function listSignals(
  limit = 50,
): Promise<SignalWithChannel[]> {
  const client = getSupabase();
  const { data, error } = await client
    .from("signals")
    .select("*, channel:channels(name, telegram_id)")
    .order("created_at", { ascending: false })
    .limit(limit);

  if (error) {
    console.error("[signals] list failed", error);
    return [];
  }
  return (data ?? []) as SignalWithChannel[];
}
