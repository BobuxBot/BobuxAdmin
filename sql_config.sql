CREATE TABLE IF NOT EXISTS warns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_id INTEGER NOT NULL,
    moderator_id INTEGER NOT NULL,
    assigned_at INTEGER NOT NULL,
    reason TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tempbans (
    guild_id INTEGER NOT NULL,
    target_id INTEGER NOT NULL,
    unban_time INTEGER NOT NULL
);