import sqlite3
import os

import config

def run_sql_commands(cursor, path, filename):
    """Executes SQL commands from a file."""
    try:
        # Open and read the SQL file
        with open(os.path.join(path, filename), 'r') as file:
            sql_script = file.read()

        # Execute the SQL script
        cursor.executescript(sql_script)
        print(f"Successfully executed SQL script: {filename}")

    except FileNotFoundError:
        print(f"Error: File {filename} not found.")
    except sqlite3.Error as e:
        print(f"SQLite error while executing {filename}: {e}")
    except Exception as e:
        print(f"An error occurred while executing {filename}: {e}")

def run_sql_scripts(database_path, sql_scripts_path, sql_files):
    """Executes SQL scripts from a list."""
    # Connect to the database
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        print("Database connection successful.")

        # Execute each SQL file in the list
        for sql_file in sql_files:
            run_sql_commands(cursor, sql_scripts_path, sql_file)

        # Commit changes
        conn.commit()
        print("Changes committed successfully.")

    except sqlite3.Error as e:
        print(f"SQLite connection error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    finally:
        # Ensure the connection is closed
        if conn:
            conn.close()
            print("Database connection closed.")

def initialize_db(database_path, sql_scripts_path):
    # Get a list of all files in the SQL scripts directory
    sql_files = ['drop_tables.sql', 'create_tables.sql']

    # Run all the scripts
    run_sql_scripts(database_path, sql_scripts_path, sql_files)

# Run the main function
if __name__ == "__main__":
    initialize_db(config.DATABASE_PATH, config.SQL_SCRIPTS_PATH)
