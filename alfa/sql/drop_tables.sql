-- Turn off foreign key checks to avoid issues with dependent tables
PRAGMA foreign_keys = OFF;

DROP TABLE IF EXISTS position;
DROP TABLE IF EXISTS portfolio;
DROP TABLE IF EXISTS stock_to_watch;
DROP TABLE IF EXISTS price;
DROP TABLE IF EXISTS stock;
DROP TABLE IF EXISTS txn;

-- Turn foreign key checks back on
PRAGMA foreign_keys = ON;
