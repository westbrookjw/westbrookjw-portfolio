PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS checkpoints (
  provider TEXT PRIMARY KEY,
  checkpoint TEXT,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  provider TEXT NOT NULL,
  provider_message_id TEXT NOT NULL,
  message_hash TEXT NOT NULL,
  received_at TEXT NOT NULL,
  from_email TEXT NOT NULL,
  subject TEXT NOT NULL,
  snippet TEXT,
  importance TEXT NOT NULL,
  confidence REAL,
  reason_codes TEXT NOT NULL,
  llm_rationale TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(provider, provider_message_id)
);

CREATE TABLE IF NOT EXISTS alerts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  dedupe_key TEXT NOT NULL UNIQUE,
  provider TEXT NOT NULL,
  provider_message_id TEXT NOT NULL,
  importance TEXT NOT NULL,
  channel TEXT NOT NULL,
  sent_at TEXT NOT NULL,
  payload_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_received_at ON messages(received_at);
CREATE INDEX IF NOT EXISTS idx_alerts_sent_at ON alerts(sent_at);
