import { NextRequest, NextResponse } from "next/server";
import { getBot } from "@/services/telegram";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const bot = getBot();
    await bot.handleUpdate(body);
    return NextResponse.json({ ok: true });
  } catch (err) {
    console.error("[api/telegram] webhook error", err);
    return NextResponse.json(
      { ok: false, error: (err as Error).message },
      { status: 500 },
    );
  }
}

export async function GET() {
  return NextResponse.json({
    service: "signalos-telegram-webhook",
    status: "ready",
    hint: "POST Telegram updates to this endpoint.",
  });
}
