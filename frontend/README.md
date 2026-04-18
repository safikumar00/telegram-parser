# SignalOS — Phase 1 + Phase 2

Phase 1 · **Signal Ingestion** — Telegram → deterministic parser → Supabase.
Phase 2 · **Profit Engine** — pending signals → evaluated outcomes → channel analytics.

---

## Stack

- Next.js 14 (App Router) · TypeScript (strict)
- Tailwind CSS · shadcn/ui
- Supabase (Postgres)
- Telegraf · Binance public ticker

---

## Folder structure

```
signal-os/                 (this app lives in /app/frontend)
├── app/
│   ├── (landing)/
│   │   ├── page.tsx
│   │   └── layout.tsx
│   ├── dashboard/
│   │   ├── page.tsx                 ← upgraded in Phase 2
│   │   └── layout.tsx
│   ├── api/
│   │   ├── telegram/route.ts        ← Telegram webhook (Phase 1)
│   │   ├── signals/route.ts         ← read API (Phase 1)
│   │   └── cron/
│   │       └── process/route.ts     ← Phase 2 · evaluator cron
│   ├── globals.css
│   └── layout.tsx
├── components/
│   ├── ui/                          ← shadcn primitives
│   └── dashboard/
│       ├── signals-table.tsx        ← status colours + result %
│       ├── channel-performance.tsx  ← Phase 2
│       ├── processor-controls.tsx   ← Phase 2 · manual cron trigger
│       └── parser-playground.tsx
├── lib/
│   ├── supabase.ts
│   ├── parser.ts
│   └── utils.ts
├── services/
│   ├── telegram.ts                  ← Phase 1
│   ├── signals.ts                   ← Phase 1
│   ├── channels.ts                  ← Phase 1
│   ├── prices.ts                    ← Phase 2 · Binance
│   ├── evaluator.ts                 ← Phase 2 · pure eval logic
│   ├── processor.ts                 ← Phase 2 · cron driver
│   └── stats.ts                     ← Phase 2 · channel analytics
├── scripts/
│   └── worker.ts                    ← Phase 2 · Node interval fallback
├── types/index.ts
├── vercel.json                      ← Phase 2 · Vercel Cron config
├── .env.local
├── tailwind.config.ts
└── components.json
```

---

## 1 · Environment variables

```
NEXT_PUBLIC_SUPABASE_URL=https://<project>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon-key>
TELEGRAM_BOT_TOKEN=<bot-token>
CRON_SECRET=<random-string>              # optional, recommended for Phase 2
PROCESSOR_INTERVAL_MS=180000             # optional, worker-only (default 3 min)
```

`CRON_SECRET` is checked by `/api/cron/process`:
- `Authorization: Bearer <CRON_SECRET>` (Vercel Cron format), or
- `?secret=<CRON_SECRET>` in the URL.

---

## 2 · Supabase schema

### Phase 1 (baseline)

```sql
create table channels (
  id uuid primary key default gen_random_uuid(),
  name text,
  telegram_id text unique,
  created_at timestamp default now()
);

create table signals (
  id uuid primary key default gen_random_uuid(),
  channel_id uuid references channels(id),
  pair text,
  entry float,
  stop_loss float,
  take_profit float,
  status text default 'pending',
  created_at timestamp default now()
);
```

### Phase 2 (migration)

Add two columns to `signals`, plus a materialized stats table.

```sql
alter table signals add column if not exists result_percent float;
alter table signals add column if not exists closed_at timestamp;

create table if not exists channel_stats (
  id uuid primary key default gen_random_uuid(),
  channel_id uuid references channels(id) unique,
  win_rate float,
  avg_profit float,
  total_trades int,
  updated_at timestamp default now()
);

-- Keep pending-scan cheap on very large ledgers
create index if not exists signals_status_idx on signals(status);
create index if not exists signals_channel_idx on signals(channel_id);
```

The `unique` constraint on `channel_stats.channel_id` lets the processor
`upsert` with `onConflict: "channel_id"` — no duplicate rows.

---

## 3 · Evaluator contract

`evaluateSignal(signal, currentPrice)` is a **pure function**.

| Scenario                           | Output status | result_percent                               |
|------------------------------------|---------------|----------------------------------------------|
| `currentPrice >= take_profit`      | `win`         | `((TP - entry) / entry) * 100`, rounded 2dp  |
| `currentPrice <= stop_loss`        | `loss`        | `((SL - entry) / entry) * 100`, rounded 2dp  |
| neither                            | `pending`     | `null`                                       |
| already closed (`status != pending`) | unchanged   | `null` (caller ignores)                      |
| invalid inputs (null/NaN)          | `pending`     | `null`                                       |

### Test matrix (verified)

Signal: `BTCUSDT entry 62000 SL 61500 TP 64000`

| Price  | Status   | result_percent |
|--------|----------|----------------|
| 64000  | `win`    | `+3.23`        |
| 61500  | `loss`   | `-0.81`        |
| 63000  | `pending`| `null`         |

---

## 4 · Price service (Binance)

`getCurrentPrice(pair)` hits `GET https://api.binance.com/api/v3/ticker/price?symbol=...`.

- `normalizePair()`: `BTC` → `BTCUSDT`, `BTC/USDT` → `BTCUSDT`, `ethusdc` → `ETHUSDC`.
- 4-second AbortController timeout. No retries — the next cron tick is the retry.
- Returns `null` on any failure (network, HTTP 4xx/5xx, invalid pair, parse).

> Note: Binance blocks some cloud regions with HTTP 451. If you see that, route
> the processor through a region Binance allows (Vercel default regions work)
> or swap in CoinGecko by reimplementing `getCurrentPrice`.

---

## 5 · Processor (cron)

`processSignals()` runs the strict pipeline for every pending row:

```
fetch pending (limit 200)
  → for each:
      Processing signal        ← console.log
      Fetched price            ← console.log
      Evaluation result        ← console.log
      DB update result         ← console.log (guarded on status='pending')
  → refresh channel_stats for each touched channel
```

**Concurrency-safe update:** the `UPDATE` filters by `id` **and** `status='pending'`
so a second concurrent runner cannot re-close the same signal.

### Option A — Vercel Cron (preferred)

`vercel.json` already contains:

```json
{ "crons": [{ "path": "/api/cron/process", "schedule": "*/3 * * * *" }] }
```

Set `CRON_SECRET` in Vercel → Settings → Environment Variables. Vercel Cron
sends `Authorization: Bearer <CRON_SECRET>` automatically.

### Option B — Supabase Edge Function (scheduled)

```ts
// supabase/functions/process-signals/index.ts
Deno.serve(async () => {
  const r = await fetch(`${Deno.env.get("APP_URL")}/api/cron/process`, {
    method: "POST",
    headers: { Authorization: `Bearer ${Deno.env.get("CRON_SECRET")}` },
  });
  return new Response(await r.text(), { status: r.status });
});
```

Schedule with `supabase functions schedule create process-signals --cron "*/3 * * * *"`.

### Option C — Node interval worker (self-hosted)

```
yarn worker
```

Runs `processSignals()` every `PROCESSOR_INTERVAL_MS` (default 3 min).

---

## 6 · Channel stats

`computeChannelStats(channel_id)` returns:

```ts
{
  win_rate:    (wins / closed_trades) * 100,   // rounded 2dp
  avg_profit:  mean(result_percent),           // rounded 2dp
  total_trades: closed_trades_count,           // pending excluded
}
```

`refreshChannelStats(channel_id)` additionally upserts into `channel_stats`
so the dashboard reads pre-aggregated rows instead of scanning `signals`.

`listChannelStats()` joins `channel_stats` with `channels` for the UI.

---

## 7 · Run / build

```bash
cd /app/frontend
yarn install
yarn dev         # next dev -H 0.0.0.0 -p 3000
yarn build       # production build
yarn worker      # optional: local cron worker
```

Pages:

- `/` — landing
- `/dashboard` — ledger + stats + parser sandbox + manual "Run processor now"
- `POST /api/telegram` — ingestion webhook
- `GET /api/signals` — ledger JSON
- `GET|POST /api/cron/process` — evaluator cron (secret-protected if set)

---

## 8 · Debugging Phase 2

- **Processor updates 0 rows**
  - Binance reachable? Watch for `[prices] ... HTTP 451` in logs.
  - Column exists? Rerun the Phase 2 migration in Supabase SQL.
- **Processor closes the same signal twice**
  - Impossible by design — the UPDATE filter includes `status='pending'`.
    If you saw duplicates, check for manual SQL edits.
- **Channel performance empty**
  - It's populated only after the processor closes at least one signal.
    Click **Run processor now** on the dashboard once there's a live pending row.
- **Vercel Cron silent**
  - Vercel dashboard → Cron logs. Ensure `CRON_SECRET` matches your env.
- **Want to force-reset a signal for testing**

  ```sql
  update signals set status='pending', result_percent=null, closed_at=null
  where id = '<uuid>';
  ```

---

Phase 3 (execution bridge, per-channel PnL replay) builds on `channel_stats`.
Don't widen the signal schema further here — migrate in a Phase 3 PR.
