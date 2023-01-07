CREATE TABLE IF NOT EXISTS warns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_id INT NOT NULL,
    moderator_id INT NOT NULL,
    assigned_at INT NOT NULL,
    reason TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tempbans (
    target_id INT NOT NULL,
    unban_time INT NOT NULL
);

CREATE TABLE IF NOT EXISTS bugpoints (
    id INT PRIMARY KEY,
    points INT NOT NULL DEFAULT 0 CHECK (points >= 0)
);

CREATE TABLE IF NOT EXISTS suggestionpoints (
    id INT PRIMARY KEY,
    points INT NOT NULL DEFAULT 0 CHECK (points >= 0)
);
