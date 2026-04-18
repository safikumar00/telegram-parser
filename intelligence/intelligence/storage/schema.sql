-- intelligence.db schema
-- Pure SQL so it's trivially portable to Postgres (just drop the `AUTOINCREMENT`).

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS groups (
  id                 INTEGER PRIMARY KEY AUTOINCREMENT,
  telegram_id        INTEGER NOT NULL UNIQUE,
  title              TEXT    NOT NULL,
  username           TEXT,
  last_message_id    INTEGER NOT NULL DEFAULT 0,
  created_at         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
  id                 INTEGER PRIMARY KEY AUTOINCREMENT,
  telegram_id        INTEGER NOT NULL UNIQUE,
  username           TEXT,
  display_name       TEXT,
  created_at         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
  id                   INTEGER PRIMARY KEY AUTOINCREMENT,
  telegram_id          INTEGER NOT NULL,
  group_telegram_id    INTEGER NOT NULL,
  sender_telegram_id   INTEGER,
  text                 TEXT    NOT NULL,
  message_type         TEXT    NOT NULL DEFAULT 'text',
  sent_at              TIMESTAMP NOT NULL,
  reply_to             INTEGER,
  raw_meta             TEXT, -- JSON blob
  created_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (group_telegram_id, telegram_id)
);
CREATE INDEX IF NOT EXISTS idx_messages_group_sent ON messages(group_telegram_id, sent_at);
CREATE INDEX IF NOT EXISTS idx_messages_sender     ON messages(sender_telegram_id);

CREATE TABLE IF NOT EXISTS signals (
  id                   INTEGER PRIMARY KEY AUTOINCREMENT,
  rule_name            TEXT    NOT NULL,
  message_id           INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
  group_telegram_id    INTEGER NOT NULL,
  matched_conditions   TEXT    NOT NULL, -- JSON array
  confidence           REAL    NOT NULL DEFAULT 1.0,
  created_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (rule_name, message_id)
);
CREATE INDEX IF NOT EXISTS idx_signals_rule  ON signals(rule_name);
CREATE INDEX IF NOT EXISTS idx_signals_group ON signals(group_telegram_id);

CREATE TABLE IF NOT EXISTS summaries (
  id                   INTEGER PRIMARY KEY AUTOINCREMENT,
  group_telegram_id    INTEGER NOT NULL,
  covers_from          TIMESTAMP NOT NULL,
  covers_to            TIMESTAMP NOT NULL,
  message_count        INTEGER NOT NULL,
  text                 TEXT    NOT NULL,
  model                TEXT    NOT NULL,
  created_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_summaries_group ON summaries(group_telegram_id, covers_to);
