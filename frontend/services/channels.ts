import { getSupabase } from "@/lib/supabase";
import type { Channel } from "@/types";
import type { Context } from "telegraf";

/**
 * Resolves a Telegram chat to a `channels` row, creating one if needed.
 *
 * Uses upsert on `telegram_id` so duplicate webhook deliveries do not
 * create duplicate channels.
 */
export async function getOrCreateChannel(
  ctx: Context,
): Promise<Channel | null> {
  const chat = ctx.chat;
  if (!chat) {
    console.warn("[channels] ctx.chat missing");
    return null;
  }

  const telegram_id = String(chat.id);
  const name =
    "title" in chat && chat.title
      ? chat.title
      : "username" in chat && chat.username
      ? `@${chat.username}`
      : "first_name" in chat && chat.first_name
      ? chat.first_name
      : "Unknown";

  const client = getSupabase();

  const { data, error } = await client
    .from("channels")
    .upsert(
      { telegram_id, name },
      { onConflict: "telegram_id", ignoreDuplicates: false },
    )
    .select()
    .single();

  if (error) {
    console.error("[channels] upsert failed", error);
    return null;
  }
  return data as Channel;
}
