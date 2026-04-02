# Local-First Email Triage Daemon (Fastmail + Gmail + Ollama)

## 1) Architecture overview
- **Connectors layer**: `FastmailJmapConnector` and `GmailApiConnector` poll inboxes for new messages.
- **Normalization layer**: Provider-specific payloads are mapped into one `NormalizedMessage` model.
- **Rules layer**: deterministic sender/domain/keyword policy runs first.
- **Classifier layer**: `OllamaClassifier` is called only when pre-rules set `needs_llm=True`.
- **Decision & notification layer**: messages are categorized into `critical|important|normal|ignore` and only policy-allowed events are sent.
- **Persistence layer**: SQLite stores checkpoints, messages, and alerts for idempotency and history.
- **Runtime**: single long-lived polling process (`main.py`) with retry/backoff and structured logs.

## 2) Data flow
1. Poll provider using saved checkpoint.
2. Normalize each raw message into `NormalizedMessage`.
3. Evaluate deterministic rules.
4. Optional LLM classification.
5. Save message + decision record.
6. Evaluate quiet hours + notify policy.
7. De-duplicate alert by `dedupe_key`.
8. Send push notification and persist alert.
9. Advance provider checkpoint.

## 3) Normalized message model
Defined in `email_triage_daemon/models.py` (`NormalizedMessage`) with:
- provider, provider_message_id, thread_id
- timestamps (`received_at`, `sent_at`)
- sender/recipient fields (`from_email`, `to_emails`, `cc_emails`)
- content (`subject`, `snippet`, `body_text`, `body_html`)
- flags/metadata (`labels`, `has_attachments`, `message_hash`)

## 4) SQLite schema
Located at `email_triage_daemon/persistence/schema.sql`:
- `checkpoints(provider, checkpoint, updated_at)`
- `messages(... importance, confidence, reason_codes, llm_rationale ...)`
- `alerts(dedupe_key UNIQUE, provider, provider_message_id, importance, channel, sent_at, payload_json)`

## 5) Configuration schema
Typed Pydantic schema in `email_triage_daemon/config.py`:
- `polling`
- `quiet_hours`
- `notifications`
- `rules`
- `ollama`
- `sqlite_path`, `log_level`

Example policy file: `config/policy.example.yaml`.

## 6) Classifier prompt design (local LLM)
Prompt is split into:
- system prompt with strict behavior constraints
- user prompt containing normalized fields and category rubric

Implemented in `email_triage_daemon/classifier/prompt.py`.

## 7) Strict JSON response contract
Expected keys:
```json
{
  "importance": "critical|important|normal|ignore",
  "confidence": 0.0,
  "rationale": "string <= 280 chars",
  "categories": ["billing", "security"],
  "action_deadline": "immediate|today|this_week|none"
}
```
Validated by Pydantic model `LLMClassification`.

## 8) Notification contract
`AlertEvent` fields in `models.py`:
- `dedupe_key`
- `importance`
- `title`, `body`
- `source_message_id`, `source_provider`
- `policy_tags`
- `created_at`

Notifiers:
- `NtfyNotifier`
- `PushoverNotifier`

## 9) Project file tree
```text
email_triage_daemon/
  __init__.py
  main.py
  config.py
  models.py
  logging_config.py
  normalization.py
  rules.py
  connectors/
    base.py
    fastmail_jmap.py
    gmail_api.py
  classifier/
    prompt.py
    ollama_client.py
  notifier/
    base.py
    ntfy.py
    pushover.py
  persistence/
    db.py
    repository.py
    schema.sql
  utils/
    retry.py
config/
  policy.example.yaml
pyproject.toml
README_EMAIL_TRIAGE.md
```

## 10) Starter code notes
- Fully typed Python 3.12 code with docstrings.
- Error handling on network calls and message processing paths.
- No hardcoded credentials (all provider/notification secrets via env vars).
- Polling-oriented v1 daemon loop and persistence-backed dedupe/checkpoints.
