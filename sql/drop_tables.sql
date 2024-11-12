-- Disable foreign key checks temporarily
PRAGMA foreign_keys = OFF;

-- Generate and execute drop statements for all tables
BEGIN TRANSACTION;
SELECT 'DROP TABLE IF EXISTS ' || name || ';' 
FROM sqlite_master 
WHERE type = 'table';
COMMIT;

-- Re-enable foreign key checks
PRAGMA foreign_keys = ON;
