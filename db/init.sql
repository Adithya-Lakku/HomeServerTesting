CREATE TABLE IF NOT EXISTS inventory (
    id SERIAL PRIMARY KEY,
    item_name TEXT NOT NULL,
    quantity INTEGER NOT NULL
);
