CREATE TABLE IF NOT EXISTS identities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    display_name TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS platform_links (
    identity_id INTEGER NOT NULL,
    platform TEXT NOT NULL,
    platform_user_id TEXT NOT NULL,
    PRIMARY KEY (platform, platform_user_id)
);
CREATE TABLE IF NOT EXISTS link_codes (
    code TEXT PRIMARY KEY,
    identity_id INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    identity_id INTEGER NOT NULL,
    session_key TEXT NOT NULL,
    started_at TEXT NOT NULL,
    PRIMARY KEY (identity_id, session_key)
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    identity_id INTEGER NOT NULL,
    session_key TEXT NOT NULL,
    platform TEXT NOT NULL,
    role TEXT NOT NULL,
    text TEXT NOT NULL,
    ts TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cron_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    identity_id INTEGER NOT NULL,
    platform TEXT NOT NULL,
    chat_id TEXT NOT NULL,
    schedule TEXT NOT NULL,
    prompt TEXT NOT NULL,
    last_run TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backend TEXT NOT NULL,
    command TEXT NOT NULL,
    allowed INTEGER NOT NULL,
    output TEXT DEFAULT '',
    ts TEXT NOT NULL
);
