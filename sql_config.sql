CREATE TABLE IF NOT EXISTS bugpoints (
    id INT PRIMARY KEY,
    points INT NOT NULL DEFAULT 0 CHECK (points >= 0)
);
