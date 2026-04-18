import { Telegraf, Context } from "telegraf";
import type { Message } from "@telegraf/types";
import { parseSignal } from "@/lib/parser";
import { getOrCreateChannel } from "@/services/channels";
import { createSignal } from "@/services/signals";

const TOKEN = process.env.TELEGRAM_BOT_TOKEN;

let _bot: Telegraf | null = null;

/**
 * Returns a singleton Telegraf instance wired with the signal-ingestion
 * pipeline. Throws if TELEGRAM_BOT_TOKEN is not configured.
 */
export function getBot(): Telegraf {
  if (_bot) return _bot;
  if (!TOKEN) {
    throw new Error(
      "TELEGRAM_BOT_TOKEN is not set. Configure it in .env.local.",
    );
  }
  const bot = new Telegraf(TOKEN);

  bot.start((ctx) =>
    ctx.reply(
      "SignalOS bot online. Add me to a channel / group as an admin and I will ingest trading signals posted there.",
    ),
  );

  bot.command("ping", (ctx) => ctx.reply("pong"));

  // Listen to text messages + channel posts (channels don't fire `on('text')`).
  bot.on(["text", "channel_post"], handleMessage);

  _bot = bot;
  return bot;
}

async function handleMessage(ctx: Context) {
  try {
    const message =
      (ctx.message as Message.TextMessage | undefined)?.text ??
      (ctx.channelPost as Message.TextMessage | undefined)?.text ??
      "";

    console.log("[telegram] Incoming message:", message);
    if (!message) return;

    const parsed = parseSignal(message);
    console.log("[telegram] Parsed signal:", parsed);

    if (!parsed.pair || parsed.entry === null) {
      console.log("[telegram] Ignored — not a valid signal");
      return;
    }

    const channel = await getOrCreateChannel(ctx);
    console.log("[telegram] Channel:", channel);

    const result = await createSignal({
      channel_id: channel?.id ?? null,
      pair: parsed.pair,
      entry: parsed.entry,
      stop_loss: parsed.stop_loss,
      take_profit: parsed.take_profit,
    });
    console.log("[telegram] DB insert result:", result);
  } catch (err) {
    console.error("[telegram] handler error", err);
  }
}

export const isBotConfigured = (): boolean => Boolean(TOKEN);
