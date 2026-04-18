/**
 * Robust signal parser for Telegram trading messages.
 *
 * Handles messy real-world formats:
 *   • "🔥 BTC/USDT LONG Entry: 62000 - 62500 SL: 61500 TP1: 63000 TP2: 64000"
 *   • "BUY BTC 62000 SL 61500 TP 64000"
 *   • "ETH/USDT Entry 3200 Stop Loss 3100 Take Profit 3400"
 *
 * Rules:
 *   • Normalize (uppercase, strip emojis/symbols).
 *   • Pair supports BTC, BTCUSDT, BTC/USDT (returned without slash).
 *   • Entry range "62000 - 62500" → first value.
 *   • Multiple TPs → highest value.
 *   • Invalid messages return all nulls.
 */

export interface ParsedSignal {
  pair: string | null;
  entry: number | null;
  stop_loss: number | null;
  take_profit: number | null;
}

const KNOWN_QUOTES = ["USDT", "USDC", "USD", "BUSD", "BTC", "ETH", "EUR"];

// Common trading tickers we recognize as pairs on their own (BTC → BTCUSDT? No —
// spec says "BTC" is a valid pair form, so we keep it as-is when unadorned).
const KNOWN_BASES = [
  "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "AVAX", "DOT",
  "MATIC", "LINK", "LTC", "TRX", "NEAR", "ATOM", "ARB", "OP", "APT",
  "FIL", "ETC", "UNI", "ICP", "HBAR", "XLM", "SUI", "TON", "SHIB",
  "PEPE", "INJ", "RUNE", "SEI", "TIA", "WLD", "FET", "RNDR", "IMX",
];

function normalize(input: string): string {
  if (!input) return "";
  // Strip emojis & pictographs (BMP + astral planes)
  const stripped = input.replace(
    // eslint-disable-next-line no-misleading-character-class
    /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}\u{1F000}-\u{1F2FF}\u{FE0F}]/gu,
    " ",
  );
  // Replace other decorative symbols, keep letters/digits/./-/:/space/slash
  const cleaned = stripped.replace(/[^\w\s.\-:/]/g, " ");
  return cleaned.toUpperCase().replace(/\s+/g, " ").trim();
}

function extractPair(msg: string): string | null {
  // 1. BASE/QUOTE format → return as BASEQUOTE (no slash)
  const slashMatch = msg.match(/\b([A-Z]{2,10})\s*\/\s*([A-Z]{2,10})\b/);
  if (slashMatch) {
    return `${slashMatch[1]}${slashMatch[2]}`;
  }

  // 2. BASEQUOTE concatenated (e.g. BTCUSDT)
  const concatRegex = new RegExp(
    `\\b([A-Z]{2,10})(${KNOWN_QUOTES.join("|")})\\b`,
  );
  const concat = msg.match(concatRegex);
  if (concat) {
    return `${concat[1]}${concat[2]}`;
  }

  // 3. Bare base ticker (e.g. "BUY BTC 62000")
  const bareRegex = new RegExp(`\\b(${KNOWN_BASES.join("|")})\\b`);
  const bare = msg.match(bareRegex);
  if (bare) return bare[1];

  return null;
}

function firstNumber(str: string): number | null {
  const m = str.match(/-?\d+(?:[.,]\d+)?/);
  if (!m) return null;
  const n = Number(m[0].replace(",", "."));
  return Number.isFinite(n) ? n : null;
}

function allNumbers(str: string): number[] {
  const matches = str.match(/-?\d+(?:[.,]\d+)?/g) ?? [];
  return matches
    .map((x) => Number(x.replace(",", ".")))
    .filter((n) => Number.isFinite(n));
}

function sliceAround(msg: string, index: number, len: number, window = 40): string {
  return msg.slice(index + len, Math.min(index + len + window, msg.length));
}

function extractEntry(msg: string): number | null {
  // Match labels: ENTRY, ENTRY:, ENTRY PRICE, BUY, LONG, SHORT, SELL @, ...
  const labelRegex =
    /\b(ENTRY(?:\s*PRICE)?|BUY|SELL|LONG|SHORT|OPEN)\b[:\s@]*/;
  const m = msg.match(labelRegex);
  if (m && m.index !== undefined) {
    const after = sliceAround(msg, m.index, m[0].length);
    // Range: "62000 - 62500" → first
    const range = after.match(/(-?\d+(?:[.,]\d+)?)\s*-\s*(-?\d+(?:[.,]\d+)?)/);
    if (range) return Number(range[1].replace(",", "."));
    return firstNumber(after);
  }
  // No explicit label → first number that isn't near SL/TP
  return null;
}

function extractStopLoss(msg: string): number | null {
  const m = msg.match(/\b(SL|S\/L|STOP\s*LOSS|STOPLOSS|STOP)\b[:\s@]*/);
  if (!m || m.index === undefined) return null;
  const after = sliceAround(msg, m.index, m[0].length);
  return firstNumber(after);
}

function extractTakeProfit(msg: string): number | null {
  // Collect all TPs (TP, TP1, TP2, TAKE PROFIT, TARGET, ...)
  const tpRegex =
    /\b(TP\d*|T\/P|TAKE\s*PROFIT|TAKEPROFIT|TARGET\s*\d*|TGT\s*\d*)\b[:\s@]*/g;
  const values: number[] = [];
  let match: RegExpExecArray | null;
  while ((match = tpRegex.exec(msg)) !== null) {
    const after = sliceAround(msg, match.index, match[0].length, 24);
    const nums = allNumbers(after);
    if (nums.length > 0) values.push(nums[0]);
  }
  if (values.length === 0) return null;
  return Math.max(...values);
}

export function parseSignal(message: string): ParsedSignal {
  const empty: ParsedSignal = {
    pair: null,
    entry: null,
    stop_loss: null,
    take_profit: null,
  };
  if (!message || typeof message !== "string") return empty;

  const msg = normalize(message);
  if (!msg) return empty;

  const pair = extractPair(msg);
  const stop_loss = extractStopLoss(msg);
  const take_profit = extractTakeProfit(msg);
  let entry = extractEntry(msg);

  // Fallback entry: if label-based failed but we have a pair and at least one
  // numeric token that isn't SL/TP, take the first unattributed number.
  if (entry === null && pair) {
    // Remove segments starting at SL/TP labels to avoid picking those numbers.
    const scrubbed = msg
      .replace(/\b(SL|S\/L|STOP\s*LOSS|STOPLOSS)\b[:\s@]*-?\d+(?:[.,]\d+)?/g, " ")
      .replace(/\b(TP\d*|T\/P|TAKE\s*PROFIT|TARGET\s*\d*)\b[:\s@]*-?\d+(?:[.,]\d+)?/g, " ");
    const first = firstNumber(scrubbed);
    if (first !== null) entry = first;
  }

  // Signal is only valid if we have at minimum a pair and an entry price.
  if (!pair || entry === null) return empty;

  return { pair, entry, stop_loss, take_profit };
}
