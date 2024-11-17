import os
import sqlite3
from importlib.resources import files


def run_sql_script(cursor, sql_file):
    """Executes SQL commands from a file."""
    try:
        # Read the SQL file
        sql_script = files("alfa.sql").joinpath(sql_file).read_text()

        # Execute the SQL script
        cursor.executescript(sql_script)
        print(f"Successfully executed SQL script: {sql_file}")
        return True
    except FileNotFoundError:
        print(f"Error: File {sql_file} not found.")
        return False
    except sqlite3.Error as e:
        print(f"SQLite error while executing {sql_file}: {e}")
        return False
    except Exception as e:
        print(f"An error occurred while executing {sql_file}: {e}")
        return False


def run_sql_scripts(database_path, sql_files):
    """Executes SQL scripts from a list."""
    # Connect to the database
    try:
        with sqlite3.connect(database_path) as conn:
            cursor = conn.cursor()
            print("Database connection successful.")

            # Execute each SQL file in the list
            for sql_file in sql_files:
                if not run_sql_script(cursor, sql_file):
                    return False

            # Commit changes
            conn.commit()
            print("Changes committed successfully.")
            return True
    except sqlite3.Error as e:
        print(f"SQLite connection error: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False


def initialize_db(database_path):
    # Files in the SQL scripts directory
    sql_files = ["drop_tables.sql", "create_tables.sql"]

    # Run all the scripts
    run_sql_scripts(database_path, sql_files)


# Run the main function
if __name__ == "__main__":
    # Path to the directory and database
    dir_path = "data"
    db_path = os.path.join(dir_path, "alfa.db")

    # Check if the directory exists, and if not, create it
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"Directory '{dir_path}' created.")

    initialize_db(db_path)
