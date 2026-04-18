import { NextResponse } from "next/server";
import { listSignals } from "@/services/signals";
import { isSupabaseConfigured } from "@/lib/supabase";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function GET() {
  if (!isSupabaseConfigured()) {
    return NextResponse.json({ signals: [], configured: false });
  }
  try {
    const signals = await listSignals(100);
    return NextResponse.json({ signals, configured: true });
  } catch (err) {
    console.error("[api/signals] list failed", err);
    return NextResponse.json(
      { signals: [], configured: true, error: (err as Error).message },
      { status: 500 },
    );
  }
}
