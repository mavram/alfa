CREATE TABLE IF NOT EXISTS stock (
    id INTEGER PRIMARY KEY,
    symbol TEXT NOT NULL UNIQUE,
    company TEXT NOT NULL
    );

CREATE TABLE IF NOT EXISTS price (
    id INTEGER PRIMARY KEY,
    stock_id INTEGER,
    date NOT NULL,
    open NOT NULL,
    high NOT NULL,
    low NOT NULL,
    close NOT NULL,
    adjusted_close NOT NULL,
    volume NOT NULL,
    FOREIGN KEY (stock_id) REFERENCES stock (id)
    );

CREATE TABLE IF NOT EXISTS watchlist (
    id INTEGER PRIMARY KEY,
    stock_id INTEGER,
    FOREIGN KEY (stock_id) REFERENCES stock (id)
    );

CREATE TABLE IF NOT EXISTS portfolio (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
    );

CREATE TABLE IF NOT EXISTS position (
    id INTEGER PRIMARY KEY,
    portfolio_id INTEGER,
    stock_id INTEGER,
    date NOT NULL,
    quantity NOT NULL,
    FOREIGN KEY (portfolio_id) REFERENCES portfolio (id)
    FOREIGN KEY (stock_id) REFERENCES stock (id)
    );
