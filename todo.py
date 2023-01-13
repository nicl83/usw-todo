import sqlite3
import sys
import importlib
import logging
from pathlib import Path

# Set for development, will be commented in "final version"
logging.basicConfig(level=logging.DEBUG)

todo_database_filename = "todo.db"

def initialise_db(filename: str) -> sqlite3.Connection:
    """
    Load the database from disk and return a SQLite connection obejct.
    Will create the "todo" table if it does not exist in the database.
    """

    # Load database from disk
    logging.debug("Loading database from disk...")
    db_connection = sqlite3.connect(todo_database_filename)
    db_cursor = db_connection.cursor()

    # Check to see if "todo" table exists
    # If not, create table
    logging.debug("Checking for presence of Todo table...")
    db_cursor.execute("""
    SELECT count(name)
    FROM sqlite_master
    WHERE type='table'
    AND name='todo';
    """)

    if db_cursor.fetchone()[0] == 0:
        # Table doesn't exist, create it
        logging.debug("Todo table not found, creating it now...")
        db_cursor.execute("""
        CREATE TABLE todo (
            task_id INTEGER PRIMARY KEY,
            task_title TEXT,
            task_body TEXT,
            task_due timestamp
        );
        """)
    else:
        logging.debug("Found Todo table!")

    #...eventually
    return db_connection

def view_tasks_cli(db_connection: sqlite3.Connection):
    pass

def main_cli(db_connection: sqlite3.Connection):
    """The main function for the CLI."""
    pass

def main_gui(db_connection: sqlite3.Connection):
    """The main function for the Tk-based GUI."""
    print("Stubbed, calling CLI")
    main_cli(db_connection)

if __name__ == "__main__":
    db_connection = initialise_db(todo_database_filename)

    # Try to launch in graphical mode.
    # If this fails, fallback to a command-line interface.
    try:
        import tkinter
        main_gui(db_connection)
    except ModuleNotFoundError:
        main_cli(db_connection)