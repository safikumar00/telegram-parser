/**
 * Signal evaluation — pure function.
 *
 * Given a signal and a current market price, decide:
 *   • win    → currentPrice >= take_profit
 *   • loss   → currentPrice <= stop_loss
 *   • pending → otherwise
 *
 * Already-closed signals (status !== 'pending') are returned unchanged.
 * Invalid inputs produce an unchanged pending-style result (never throws).
 */

export interface EvaluatorInput {
  entry: number | null;
  stop_loss: number | null;
  take_profit: number | null;
  status: string;
}

export type EvaluatorStatus = "win" | "loss" | "pending";

export interface EvaluatorOutput {
  status: EvaluatorStatus;
  result_percent: number | null;
  closed_at: Date | null;
}

function round2(n: number): number {
  return Math.round(n * 100) / 100;
}

function isValid(n: unknown): n is number {
  return typeof n === "number" && Number.isFinite(n);
}

export function evaluateSignal(
  signal: EvaluatorInput,
  currentPrice: number | null,
): EvaluatorOutput {
  // Already closed? Return as-is (caller can detect "unchanged" via status).
  if (signal.status && signal.status !== "pending") {
    return {
      status: signal.status as EvaluatorStatus,
      result_percent: null,
      closed_at: null,
    };
  }

  // Bad inputs → remain pending, don't crash.
  if (
    !isValid(currentPrice) ||
    !isValid(signal.entry) ||
    signal.entry === 0
  ) {
    return { status: "pending", result_percent: null, closed_at: null };
  }

  const { entry, stop_loss, take_profit } = signal;

  // Win: require a valid TP and price reached it.
  if (isValid(take_profit) && currentPrice >= take_profit) {
    const pct = ((take_profit - entry) / entry) * 100;
    return {
      status: "win",
      result_percent: round2(pct),
      closed_at: new Date(),
    };
  }

  // Loss: require a valid SL and price reached it.
  if (isValid(stop_loss) && currentPrice <= stop_loss) {
    const pct = ((stop_loss - entry) / entry) * 100;
    return {
      status: "loss",
      result_percent: round2(pct),
      closed_at: new Date(),
    };
  }

  return { status: "pending", result_percent: null, closed_at: null };
}
