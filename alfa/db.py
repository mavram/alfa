import sqlite3
import os


def get_sql_scripts_absolute_path():
    """Returns SQL scripts absolute path."""
    python_file_relative_directory = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(python_file_relative_directory, "sql")


def run_sql_commands(cursor, path, filename):
    """Executes SQL commands from a file."""
    try:
        # Open and read the SQL file
        with open(os.path.join(path, filename), "r") as file:
            sql_script = file.read()

        # Execute the SQL script
        cursor.executescript(sql_script)
        print(f"Successfully executed SQL script: {filename}")
        return True
    except FileNotFoundError:
        print(f"Error: File {filename} not found.")
        return False
    except sqlite3.Error as e:
        print(f"SQLite error while executing {filename}: {e}")
        return False
    except Exception as e:
        print(f"An error occurred while executing {filename}: {e}")
        return False


def run_sql_scripts(database_path, sql_scripts_path, sql_files):
    """Executes SQL scripts from a list."""
    # Connect to the database
    try:
        with sqlite3.connect(database_path) as conn:
            cursor = conn.cursor()
            print("Database connection successful.")

        # Execute each SQL file in the list
        for sql_file in sql_files:
            if not run_sql_commands(cursor, sql_scripts_path, sql_file):
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
    # Get a list of all files in the SQL scripts directory
    sql_files = ["drop_tables.sql", "create_tables.sql"]

    # Run all the scripts
    run_sql_scripts(
        database_path, get_sql_scripts_absolute_path(), sql_files
    )


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
