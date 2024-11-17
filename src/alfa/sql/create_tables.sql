CREATE TABLE IF NOT EXISTS stock (
    id INTEGER PRIMARY KEY,
    symbol TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL
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

CREATE TABLE IF NOT EXISTS portfolio (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
    );

CREATE TABLE IF NOT EXISTS stock_to_watch (
    id INTEGER PRIMARY KEY,
    stock_id INTEGER,
    symbol TEXT NOT NULL UNIQUE,
    portfolio_id INTEGER,
    FOREIGN KEY (stock_id) REFERENCES stock (id)
    );

CREATE TABLE IF NOT EXISTS txn (
    id INTEGER PRIMARY KEY,
    portfolio_id INTEGER,
    timestamp NOT NULL,
    stock_id INTEGER,
    quantity NOT NULL,
    price NOT NULL,
    FOREIGN KEY (portfolio_id) REFERENCES portfolio (id),
    FOREIGN KEY (stock_id) REFERENCES stock (id)
    );

CREATE TABLE IF NOT EXISTS end_of_day_position (
    id INTEGER PRIMARY KEY,
    portfolio_id INTEGER,
    stock_id INTEGER,
    symbol TEXT NOT NULL UNIQUE,
    date NOT NULL,
    size NOT NULL,
    average_price NOT NULL,
    market_price NOT NULL,
    FOREIGN KEY (portfolio_id) REFERENCES portfolio (id),
    FOREIGN KEY (stock_id) REFERENCES stock (id)
    );
