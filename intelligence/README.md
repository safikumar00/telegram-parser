# Emergent AI — Telegram Intelligence Engine

A modular, production-grade Python system that fetches Telegram messages,
builds structured datasets, runs a deterministic rule engine to extract
signals, and (optionally) produces contextual briefs via Claude Sonnet 4.5.

The AI layer is **fully removable** — flip `SUMMARIZER_ENABLED=false` or delete
`intel/llm_summarizer.py` and the pipeline continues working unchanged.

---

## Architecture

```
/app/intelligence/
├── intelligence/
│   ├── config.py                   ← typed env loader (pydantic-settings)
│   ├── logging_setup.py            ← structured key=value stdlib logger
│   ├── pipeline.py                 ← orchestrator (ingest → extract → act → summarize)
│   │
│   ├── ingestion/                  ← message sources behind one Protocol
│   │   ├── base.py                 ←   MessageFetcher ABC + FetchOptions
│   │   ├── telethon_fetcher.py     ←   real Telegram (flood-wait safe)
│   │   └── mock_fetcher.py         ←   deterministic corpus for tests/dev
│   │
│   ├── storage/                    ← Repository abstraction (swap to Postgres later)
│   │   ├── base.py                 ←   Repository Protocol
│   │   ├── schema.sql              ←   groups / users / messages / signals / summaries
│   │   ├── sqlite_repo.py          ←   SQLite impl, thread-safe
│   │   └── models.py               ←   frozen dataclasses (domain objects)
│   │
│   ├── processing/                 ← pure, deterministic transforms
│   │   ├── normalizer.py           ←   NFKC, zero-width strip, whitespace fold
│   │   ├── tokenizer.py            ←   regex tokenizer (no nltk)
│   │   └── entities.py             ←   symbols, numbers, URLs, #tags, @mentions
│   │
│   ├── rules/                      ← declarative rule engine + config loader
│   │   ├── engine.py               ←   Rule, RuleEngine, 7 condition operators
│   │   └── loader.py               ←   JSON + YAML, per-file error isolation
│   │
│   ├── actions/                    ← side-effect registry
│   │   ├── base.py                 ←   ActionRegistry
│   │   ├── store_signal.py         ←   persists Signal row
│   │   ├── alert.py                ←   WARN-level log (wire webhook later)
│   │   └── forward.py              ←   stub for cross-channel relay
│   │
│   └── intel/                      ← the "intelligence" layer
│       ├── summarizer_base.py      ←   Summarizer Protocol + NullSummarizer + factory
│       ├── llm_summarizer.py       ←   Claude Sonnet 4.5 via Emergent Universal Key
│       ├── signal_extractor.py     ←   deterministic core + optional AI classifier hook
│       └── patterns.py             ←   PatternRegistry + SymbolFrequencyHook
│
├── rules_config/
│   ├── crypto_signals.yaml         ←   example: 4 rules
│   └── links.json                  ←   example: 1 rule
│
├── scripts/
│   ├── run_pipeline.py             ←   end-to-end example (mock-safe)
│   └── fetch_historical.py         ←   date-bounded backfill
│
├── tests/
│   └── test_pipeline.py            ←   6 tests: normalize / tokenize / entities / rules / e2e
│
├── data/                           ←   sqlite file lives here
├── .env.example
├── .env                            ←   git-ignored in real repos
└── requirements.txt
```

---

## 1 · Setup

```bash
cd /app/intelligence
pip install -r requirements.txt
cp .env.example .env                # fill in values as needed
```

Everything runs without Telegram credentials — the mock fetcher ships with a
deterministic 8-message corpus across 2 synthetic channels.

---

## 2 · Environment

```ini
# Telegram — leave blank to stay in mock mode (https://my.telegram.org for real creds)
TELEGRAM_API_ID=
TELEGRAM_API_HASH=
TELEGRAM_PHONE=
TELEGRAM_SESSION_NAME=intelligence

# Storage — swap URL when migrating to Postgres (repository is abstracted)
DATABASE_URL=sqlite:////app/intelligence/data/intelligence.db

# Summarizer — REMOVABLE AI LAYER. Flip to false to disable entirely.
SUMMARIZER_ENABLED=true
SUMMARIZER_PROVIDER=anthropic
SUMMARIZER_MODEL=claude-sonnet-4-5-20250929
SUMMARIZER_BATCH_SIZE=40
EMERGENT_LLM_KEY=sk-emergent-...          # provided by Emergent Universal Key

# Pipeline
LOG_LEVEL=INFO
RULES_DIR=/app/intelligence/rules_config
FETCH_BATCH_SIZE=200
FETCH_RATE_LIMIT_SLEEP=1.0
```

---

## 3 · Running

### Bare module (now works)

```bash
python -m intelligence                         # same as run_pipeline, mock mode
python -m intelligence.pipeline --debug        # also works — prints masked env + fetcher info
```

### Mock mode (zero creds)

```bash
python -m scripts.run_pipeline --source mock --group cryptoDesk
```

### Real Telegram

```bash
# First run — interactive terminal required so you can paste the login code
python -m scripts.list_groups                  # prints all your dialogs (IDs + usernames)

python -m scripts.run_pipeline --source telethon --group @myCryptoChannel
python -m scripts.fetch_historical --group @myCryptoChannel --until 2026-01-01
```

> **First-run Telegram login:** Telethon will send a 5-digit code to your
> Telegram app (not SMS). You MUST paste it in an interactive terminal —
> piped / non-TTY runs will see `EOFError`. Use `python -m scripts.list_groups`
> once to create the session; subsequent runs are fully non-interactive.

### Debug mode

```bash
python -m intelligence --source telethon --group @myChannel --debug
```

Emits a `loaded settings` log line with every env value, secrets masked:

```
env_file='/app/intelligence/.env' env_file_loaded=True
telegram_api_id=12345678 telegram_api_hash='abcd…(32 chars)'
telegram_phone='+491…(13 chars)' summarizer_enabled=True
emergent_llm_key='sk-emergen…(30 chars)' rules_dir_exists=True ...
```

### Strict mode

```bash
python -m intelligence --source telethon --group @x --strict
```

Exits with code `2` if Telethon is requested but any of `TELEGRAM_API_ID /
TELEGRAM_API_HASH / TELEGRAM_PHONE` is missing. Without `--strict` the
pipeline falls back to mock mode and warns loudly.

### Tests

```bash
python -m pytest tests -q
```

---

## 4 · Rule configuration

Rules live in `rules_config/` as `.yaml` or `.json`. They are deterministic,
hot-reloadable (next pipeline run), and never depend on any LLM.

```yaml
- name: crypto_signal
  action: store_signal        # name of a registered Action
  match_type: all             # "all" (AND, default) | "any" (OR)
  confidence: 0.9
  tags: [crypto, signal]
  conditions:
    - contains_any: ["BUY", "SELL", "LONG", "SHORT"]
    - has_symbol_any: ["BTC", "ETH", "SOL"]
    - min_numbers: 1
```

### Supported operators

| Operator         | Meaning                                                            |
|------------------|--------------------------------------------------------------------|
| `contains`       | substring in normalized text (case-insensitive)                    |
| `contains_any`   | OR over a list of substrings                                       |
| `contains_all`   | AND over a list of substrings                                      |
| `regex`          | `re.search` against the original text                              |
| `has_symbol`     | a known ticker appears in `entities.symbols`                       |
| `has_symbol_any` | any of a list of tickers appears                                   |
| `min_numbers`    | extracted numeric entities ≥ N                                     |
| `has_url`        | boolean — does the message contain any URL                         |

A rule passes only when **every** condition passes (`match_type: all`) or when
**any** passes (`match_type: any`).

### Adding a new action

```python
# intelligence/actions/my_action.py
from .base import Action, ActionContext

class MyAction(Action):
    name = "my_action"
    def execute(self, ctx: ActionContext) -> dict:
        ...
```

Register it in `pipeline.build_default_action_registry()` and reference it in
a rule via `action: my_action`.

---

## 5 · Removing the AI layer (important)

The AI summarizer is the **only** LLM-touching component. It lives behind a
`Summarizer` Protocol that the pipeline knows about. Three ways to disable it:

1. **Flag:** `SUMMARIZER_ENABLED=false` → factory returns `NullSummarizer`, nothing else changes.
2. **Missing key:** unset `EMERGENT_LLM_KEY` → factory downgrades to `NullSummarizer`.
3. **Delete the file:** `rm intelligence/intel/llm_summarizer.py` → `build_summarizer()`
   still works because the import is lazy and guarded. The pipeline, rule engine,
   actions, storage and ingestion are **unaffected**.

Rule-engine signals never rely on the LLM. The summarizer is write-only — its
output is stored in the `summaries` table and never fed back into signal
detection. This keeps the deterministic path cleanly separable for Phase 2
when you replace the summarizer with a fine-tuned classifier (plug via
`SignalExtractor.set_classifier`).

---

## 6 · Database schema

Portable SQL — drop `AUTOINCREMENT` and this runs on Postgres as-is.

```
groups    (telegram_id UNIQUE, title, username, last_message_id, created_at)
users     (telegram_id UNIQUE, username, display_name, created_at)
messages  (telegram_id, group_telegram_id, sender_telegram_id, text,
           message_type, sent_at, reply_to, raw_meta, created_at)
          UNIQUE(group_telegram_id, telegram_id)
          INDEX idx_messages_group_sent, idx_messages_sender
signals   (rule_name, message_id FK→messages, group_telegram_id,
           matched_conditions JSON, confidence, created_at)
          UNIQUE(rule_name, message_id)
          INDEX idx_signals_rule, idx_signals_group
summaries (group_telegram_id, covers_from, covers_to, message_count,
           text, model, created_at)
          INDEX idx_summaries_group
```

Swap the backend by replacing `SqliteRepository` with a class that implements
`storage.base.Repository` — nothing else changes.

---

## 7 · Logging

Everything is `key=value` structured so `grep` + `cut` + `awk` still work:

```
ts=2026-04-18T17:39:05 level=INFO logger=intelligence.pipeline
    msg='pipeline done' fetched=6 persisted=6 matches=7 actions_run=7
    summaries=1 errors=0 started_at=... finished_at=...
```

Telethon's own noisy logs are pinned to WARNING.

---

## 8 · Future-ready extensions (hooks already in place)

| Extension                    | Entry point                                                    |
|------------------------------|----------------------------------------------------------------|
| Real-time streaming          | Wrap `TelethonFetcher._client.on(events.NewMessage)` and feed `SignalExtractor.extract()` — no other module changes. |
| AI classifier layer          | `SignalExtractor.set_classifier(async def classifier(msg, matches) -> matches)` — refines deterministic matches.     |
| Dashboard / HTTP API         | Read-only endpoints over `Repository.list_signals()`, `list_messages()`, `list_summaries()`. |
| Multi-group aggregation      | `Repository.list_signals()` + `group_telegram_id` grouping; the schema already supports cross-group queries. |
| Postgres migration           | Implement `PostgresRepository(Repository)` — the rest is untouched. |

---

## 9 · Debugging

| Symptom                                    | Likely cause + fix                                                                                    |
|--------------------------------------------|-------------------------------------------------------------------------------------------------------|
| `python -m intelligence.pipeline` produces no output | Fixed — module now has a `__main__` that delegates to the CLI. Also `python -m intelligence` works. |
| `.env` not being picked up                 | Run with `--debug` — the first line shows `env_file_loaded=True/False`. The file must live at `/app/intelligence/.env`. Shell env vars override `.env` by design. |
| `EOFError: EOF when reading a line` (Telethon) | First-run login code prompt needs an interactive TTY. Run `python -m scripts.list_groups` once from a real shell; after that the session is cached. |
| Telethon silently falls back to mock       | `--strict` turns the fallback into a hard exit. Pure `--debug` shows `telegram_configured=False` when creds are incomplete. |
| No DB file created                         | Fixed — `repo.initialize()` now runs in `build_pipeline`, not lazily. Check `stage: db_ready` log line for the path. |
| `fetched=0 persisted=0` on first run       | Wrong `--group` identifier, or min_message_id too high. Pass `--reset-cursor`.                        |
| Rule never matches                         | Operator names are case-sensitive in YAML (`contains_any`, not `containsAny`). Check logs for `unknown condition`. |
| `emergentintegrations` import error        | Either set `SUMMARIZER_ENABLED=false` or `pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/`. |
| Telethon flood-wait                        | Fetcher backs off automatically up to 3 retries. Increase `FETCH_RATE_LIMIT_SLEEP` for busier channels. |
| `summarizer llm call failed: Budget has been exceeded` | Emergent Universal Key ran out of credit — flip `SUMMARIZER_ENABLED=false`, or top up at Profile → Universal Key → Add Balance. The rule engine keeps working regardless. |
| Duplicate signals                          | Impossible by design — `signals(rule_name, message_id)` is UNIQUE. Any dup means you changed the schema manually. |
