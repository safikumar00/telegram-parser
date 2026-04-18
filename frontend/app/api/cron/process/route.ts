import { NextRequest, NextResponse } from "next/server";
import { processSignals } from "@/services/processor";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";
export const maxDuration = 60;

/**
 * Cron endpoint — evaluates pending signals.
 *
 * Secured with CRON_SECRET if set. Accepts:
 *   • `Authorization: Bearer <CRON_SECRET>`  (Vercel Cron default), or
 *   • `?secret=<CRON_SECRET>` in the URL.
 *
 * Vercel Cron example (vercel.json):
 *   { "crons": [{ "path": "/api/cron/process", "schedule": "every 3 minutes" }] }
 */
export async function GET(req: NextRequest) {
  return handle(req);
}

export async function POST(req: NextRequest) {
  return handle(req);
}

async function handle(req: NextRequest) {
  const secret = process.env.CRON_SECRET;
  if (secret) {
    const auth = req.headers.get("authorization") ?? "";
    const url = new URL(req.url);
    const qp = url.searchParams.get("secret") ?? "";
    const ok =
      auth === `Bearer ${secret}` || qp === secret;
    if (!ok) {
      return NextResponse.json(
        { ok: false, error: "unauthorized" },
        { status: 401 },
      );
    }
  }

  try {
    const result = await processSignals();
    return NextResponse.json({ ok: true, ...result });
  } catch (err) {
    console.error("[api/cron] processor failed", err);
    return NextResponse.json(
      { ok: false, error: (err as Error).message },
      { status: 500 },
    );
  }
}
