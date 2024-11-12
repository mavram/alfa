import sqlite3
import os

def get_sql_files(path):
    """Returns a list of SQL filenames from the specified directory."""
    try:
        # Get all .sql files from the directory
        sql_files = [os.path.join(path, f) for f in os.listdir(path) if f.endswith('.sql')]
        return sql_files
    except FileNotFoundError:
        print(f"Error: Directory {path} not found.")
        return []
    except Exception as e:
        print(f"An error occurred while listing SQL files: {e}")
        return []

def run_sql(cursor, filename):
    """Executes SQL commands from a file."""
    try:
        # Open and read the SQL file
        with open(filename, 'r') as file:
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

def initialize_db():
    # Path to the directory containing SQL files
    sql_directory = 'sql'

    # Get a list of all files in the SQL scripts directory
    sql_files = get_sql_files(sql_directory)

    # Connect to the database
    try:
        conn = sqlite3.connect('alfa.db')
        cursor = conn.cursor()
        print("Database connection successful.")

        # Execute each SQL file in the list
        for sql_file in sql_files:
            run_sql(cursor, sql_file)

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

# Run the main function
if __name__ == "__main__":
    initialize_db()