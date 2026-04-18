# SignalOS — PRD

## Problem statement (verbatim)

Build Phase 1 (Signal Ingestion System - Hardened Version) of SaaS product SignalOS.
Telegram trading signals → structured storage for analytics. Next.js 14 App Router,
TypeScript strict, Tailwind, shadcn/ui (MCP registry), Supabase (Postgres),
Telegraf. Robust parser supporting emojis, entry ranges, multi-TP. Channel
provenance via upsert on telegram_id. Strict pipeline with logs at every step.

## Architecture

- **App location:** `/app/frontend` (Next.js 14, served by supervisor on :3000)
- **Landing route:** `/` (route group `(landing)`)
- **Dashboard route:** `/dashboard` (moved out of `(dashboard)` group to avoid root-route collision)
- **Webhook route:** `POST /api/telegram` — Telegraf `handleUpdate`
- **Read API:** `GET /api/signals` — list for dashboard
- **DB:** Supabase Postgres, tables `channels`, `signals` (schema in README §2)

## Tasks done (2026-02-xx, Phase 1 MVP)

- [x] Replaced React+FastAPI template with Next.js 14 + TS strict
- [x] `components.json` with shadcn MCP registry pointing at tweakcn themes
- [x] shadcn components copied inline: button, card, badge, input, table
- [x] `lib/parser.ts` — deterministic regex parser (normalize, BASE/QUOTE, range, multi-TP)
- [x] `lib/supabase.ts` — lazy singleton; clear error when unset
- [x] `services/telegram.ts` — Telegraf singleton; handles `text` + `channel_post`
- [x] `services/channels.ts` — `getOrCreateChannel(ctx)` with `upsert(telegram_id)`
- [x] `services/signals.ts` — `createSignal(...)` + `listSignals(...)`
- [x] `app/api/telegram/route.ts` — `runtime = nodejs`, POST handler, GET status
- [x] Landing page — premium glassmorphic hero, terminal preview, features, pipeline, CTA
- [x] Dashboard page — stats, signals table (shadcn Table + Badge), parser sandbox (client)
- [x] README with schema, webhook setup, BotFather steps, debugging guide
- [x] Parser validated against the specified test case + 5 additional real-world inputs

## Tasks done (2026-02-xx, Phase 2 — Profit Engine)

- [x] Schema migration documented: `signals.result_percent`, `signals.closed_at`, `channel_stats` table + indexes
- [x] `services/prices.ts` — Binance `getCurrentPrice(pair)` with `normalizePair()`, AbortController timeout, null-on-failure
- [x] `services/evaluator.ts` — pure `evaluateSignal(signal, price)`: win / loss / pending, 2-decimal result_percent
- [x] `services/processor.ts` — `processSignals()` with concurrency-guarded UPDATE (`status='pending'` filter) + touched-channel stats refresh
- [x] `services/stats.ts` — `computeChannelStats`, `refreshChannelStats`, `listChannelStats`
- [x] `/api/cron/process` route (`runtime=nodejs`, `maxDuration=60`, `CRON_SECRET` bearer/query support)
- [x] `vercel.json` with `*/3 * * * *` cron on `/api/cron/process`
- [x] `scripts/worker.ts` — Node `setInterval` fallback, `yarn worker`
- [x] Dashboard upgrade — 5 KPIs (Ingested, Channels, Wins, Losses, Win rate), coloured status badges, result %, closed_at, `ProcessorControls` client component, `ChannelPerformance` panel
- [x] Evaluator verified against the spec matrix: @64000 → win +3.23%, @61500 → loss -0.81%, @63000 → pending ✓

## Core requirements (static)

1. Deterministic parser, no AI APIs.
2. Strict pipeline: log → parse → validate → resolve channel → store → log.
3. Channel upsert never duplicates on webhook retries.
4. Env-only config; no hardcoded secrets; `yarn build` must pass clean.
5. UI: glassmorphism, rounded-2xl, soft shadows, Apple-minimal.

## What's implemented

- End-to-end ingestion pipeline validated locally via `parseSignal` unit run.
- Both pages render (HTTP 200 locally and via preview URL).
- Webhook endpoint responds with service ready on GET.

## Backlog (Phase 2 seeds — not this PR)

- P0: Authenticated dashboard (multi-tenant per desk)
- P0: Execution bridge (signal → broker)
- P1: Replay engine over historical signals
- P1: PnL attribution per channel
- P2: Channel quality scoring
- P2: Signal deduplication across forwarded channels
