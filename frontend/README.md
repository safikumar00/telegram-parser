# SignalOS — Phase 1 (Signal Ingestion System)

A production-grade ingestion layer for Telegram trading signals.

Telegram → Telegraf → deterministic parser → Supabase (Postgres).

---

## Stack

- Next.js 14 (App Router) · TypeScript (strict)
- Tailwind CSS · shadcn/ui
- Supabase (Postgres + `@supabase/supabase-js`)
- Telegraf (Telegram Bot)

---

## Folder structure

```
signal-os/                 (this app lives in /app/frontend)
├── app/
│   ├── (landing)/
│   │   ├── page.tsx       ← marketing landing
│   │   └── layout.tsx
│   ├── dashboard/
│   │   ├── page.tsx       ← signal dashboard
│   │   └── layout.tsx
│   ├── api/
│   │   ├── telegram/
│   │   │   └── route.ts   ← Telegram webhook
│   │   └── signals/
│   │       └── route.ts   ← read API (for tests)
│   ├── globals.css
│   └── layout.tsx
├── components/
│   ├── ui/                ← shadcn (button, card, table, badge, input)
│   └── dashboard/         ← signals-table, parser-playground
├── lib/
│   ├── supabase.ts
│   ├── parser.ts
│   └── utils.ts
├── services/
│   ├── telegram.ts
│   ├── signals.ts
│   └── channels.ts
├── types/
│   └── index.ts
├── .env.local
├── tailwind.config.ts
└── components.json
```

---

## 1 · Environment variables

Create `.env.local`:

```
NEXT_PUBLIC_SUPABASE_URL=https://<project>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon-key>
TELEGRAM_BOT_TOKEN=<bot-token>
```

None of these have defaults in code. Missing values fail loudly at runtime.

---

## 2 · Supabase schema

Run in the Supabase SQL editor:

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

> `telegram_id` is `unique` so `getOrCreateChannel` can upsert safely.

If you enable Row-Level Security, either:
- keep RLS **off** on these tables for server-side inserts with the anon key, or
- use a service-role key from server code (update `lib/supabase.ts` accordingly).

---

## 3 · Telegram bot setup

1. **Create a bot:** DM [@BotFather](https://t.me/BotFather) → `/newbot` → copy token.
2. **Add to a channel / group** as a member.
3. **Promote to admin** (this is required).
4. **Enable message reading**: `/setprivacy` → **Disable** (so the bot can read all messages in groups).
5. Paste the token into `.env.local` as `TELEGRAM_BOT_TOKEN`.

### Webhook registration (production)

Once deployed (e.g. Vercel):

```bash
curl -s "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<your-domain>/api/telegram"
```

Verify:

```bash
curl -s "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

### Polling (local development)

The webhook handler is always available. If you want long-polling locally, add a tiny script:

```ts
// scripts/dev-bot.ts
import { getBot } from "@/services/telegram";
getBot().launch();
```

…and run it with `tsx scripts/dev-bot.ts`.

---

## 4 · Install & run

```bash
cd /app/frontend
yarn install
yarn dev         # next dev -H 0.0.0.0 -p 3000
```

Build check:

```bash
yarn build
yarn start:prod
```

Pages:

- `/` — landing
- `/dashboard` — live signal table + parser sandbox
- `/api/telegram` — webhook endpoint (POST)
- `/api/signals` — JSON read (GET)

---

## 5 · Ingestion pipeline (strict)

```
Incoming message
  → console.log "Incoming message"
  → parseSignal()
    → if pair==null || entry==null → ignore
  → getOrCreateChannel(ctx)   (upsert on telegram_id)
  → createSignal({ channel_id, pair, entry, stop_loss, take_profit })
  → console.log "DB insert result"
```

All four log lines (`Incoming message`, `Parsed signal`, `Channel`, `DB insert result`) are emitted for every message handled.

---

## 6 · Parser contract

`parseSignal(message: string) → { pair, entry, stop_loss, take_profit }`

- Uppercases + strips emojis/symbols first.
- Pair: `BTC`, `BTCUSDT`, `BTC/USDT` → returned **without** slash.
- Entry range `"62000 - 62500"` → first value.
- Multiple TPs (`TP1 / TP2 / TP3`) → highest value.
- Returns all `null` when message doesn't contain a pair + entry.

### Test case

```
"🔥 BTC/USDT LONG Entry: 62000 - 62500 SL: 61500 TP1: 63000 TP2: 64000"
```

→

```json
{ "pair": "BTCUSDT", "entry": 62000, "stop_loss": 61500, "take_profit": 64000 }
```

---

## 7 · Debugging

- **Bot posts in channel but nothing in DB**
  - Is the bot an **admin** in that channel?
  - Did you disable `/setprivacy` for groups?
  - Check `/var/log/supervisor/frontend.*.log` (local) or Vercel logs for the 4 pipeline log lines.
- **Webhook not delivering**
  - `getWebhookInfo` → look at `last_error_message`.
  - Ensure your domain is HTTPS (Telegram rejects HTTP).
- **`Supabase credentials missing`**
  - `.env.local` not loaded. Restart the dev server after editing.
- **`channels.telegram_id` conflict**
  - Migration missed the `unique` constraint — re-run the schema.

---

## 8 · Deployment notes

- All API routes live under `app/api/**` → fully Vercel-compatible.
- No secrets are hardcoded; all config comes from env vars.
- `runtime = "nodejs"` on `/api/telegram` (Telegraf requires Node APIs, not Edge).
- `reactStrictMode` is on; `yarn build` must pass cleanly before shipping.

---

Phase 2 (execution, analytics, replay) builds on these two tables. Don't extend
the schema here — migrate in a new Phase 2 PR.
