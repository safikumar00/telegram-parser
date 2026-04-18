/**
 * Price service — Binance spot ticker.
 *
 * Resilient by design:
 *   • Normalizes pair → BASEQUOTE (BTC → BTCUSDT, BTC/USDT → BTCUSDT).
 *   • AbortController timeout (4s) so a slow Binance edge never stalls the cron.
 *   • Returns `null` on any failure (network, 4xx, 5xx, invalid pair, parse).
 */

const BINANCE_URL = "https://api.binance.com/api/v3/ticker/price";
const DEFAULT_QUOTE = "USDT";
const DEFAULT_TIMEOUT_MS = 4000;

const KNOWN_QUOTES = ["USDT", "USDC", "USD", "BUSD", "BTC", "ETH", "EUR"];

export function normalizePair(input: string): string {
  if (!input) return "";
  const up = input.toUpperCase().replace(/[^A-Z]/g, ""); // strip slash, spaces, etc.
  // Already has a known quote suffix?
  if (KNOWN_QUOTES.some((q) => up.endsWith(q) && up.length > q.length)) {
    return up;
  }
  return `${up}${DEFAULT_QUOTE}`;
}

export async function getCurrentPrice(
  pair: string,
  opts: { timeoutMs?: number } = {},
): Promise<number | null> {
  const symbol = normalizePair(pair);
  if (!symbol) {
    console.warn("[prices] empty pair after normalize");
    return null;
  }

  const controller = new AbortController();
  const timeout = setTimeout(
    () => controller.abort(),
    opts.timeoutMs ?? DEFAULT_TIMEOUT_MS,
  );

  try {
    const res = await fetch(`${BINANCE_URL}?symbol=${symbol}`, {
      signal: controller.signal,
      // Never let Next.js cache price responses.
      cache: "no-store",
    });
    if (!res.ok) {
      console.warn(`[prices] ${symbol} HTTP ${res.status}`);
      return null;
    }
    const json = (await res.json()) as { symbol?: string; price?: string };
    const price = Number(json?.price);
    if (!Number.isFinite(price)) {
      console.warn(`[prices] ${symbol} returned non-numeric price`, json);
      return null;
    }
    return price;
  } catch (err) {
    console.warn(`[prices] ${symbol} fetch failed`, (err as Error).message);
    return null;
  } finally {
    clearTimeout(timeout);
  }
}
