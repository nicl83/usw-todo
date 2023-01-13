import sqlite3
import sys
import importlib
import datetime
import logging
from pathlib import Path

# Set for development, will be commented in "final version"
logging.basicConfig(level=logging.DEBUG)

# Filename for the To Do database
todo_database_filename = "todo.db"

# A timestamp for a task that will never be due.
# (SQL "timestamp" fields must contain a date and time.)
# If no time is provided, datetime will default to midnight (00:00).
never_due = datetime.datetime(year=9999, month=12, day=31)

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

def view_tasks(db_connection: sqlite3.Connection):
    """Present a command-line interface for viewing tasks."""

    cursor = db_connection.cursor()
    tasks = cursor.execute("SELECT * FROM todo").fetchall()
    cursor.close()
    
    # TODO pretty printing
    print(tasks)
    
    return

def get_datetime_from_user() -> datetime.datetime:
    """
    Get a date and time from the user.
    Used multiple times in add_task, so it has been broken out into a separate
    function to reduce repeated code.
    """
    return_datetime = None
    while return_datetime is None:
        # I could've asked for an ISO-compliant date and time here
        # but that's not very user friendly
        day = input("Enter the day it is due (1-31): ")
        month = input("Enter the month it is due (1-12): ")
        year = input("Enter the year it is due: ")
        hour = input("Enter the hour it is due (0-23, 24hr): ")
        minute = input("Enter the minute it is due (0-59): ")
        try:
            return_datetime = datetime.datetime(
                year=int(year),
                month=int(month),
                day=int(day),
                hour=int(hour),
                minute=int(minute)
            )
        except Exception as e:
            # Catch exception, show it if a developer is running the program,
            # then tell the user to try again.
            logging.debug(e)
            print("Sorry, there was an error with your input.")
            print("Please try again.")
    
    return return_datetime

def add_task(db_connection: sqlite3.Connection):
    """Add a task to the database."""
    cursor = db_connection.cursor()

    task_name = input("Enter task name: ")
    task_body = input("Enter task notes: ")

    # Loop through the next section of code until the user either
    # enters a valid date and time, or says that one isn't required
    task_due_date = None
    while task_due_date is None:
        add_due_date = input(
            "Does this task have a deadline? (Y/N): "
        ).lower() # Case is not important, discard it
        if add_due_date == 'y':
            task_due_date = get_datetime_from_user()
        elif add_due_date == 'n':
            task_due_date = never_due
    
    # Ask the user if they would like to make any changes to the task before
    # comitting it to the database.
    task_ok = False
    while not task_ok:
        print(f"Task name: {task_name}")
        print(f"Task notes: {task_body}")
        if task_due_date == never_due:
            # User has explicitly said it has no due date, don't show it.
            pass
        else:
            print(f"Task due date: {task_due_date}")
        
        # Ask the user if they want to change anything before it is committed.
        valid_changes = ("name", "notes", "date", "ok")
        change_command = None
        while change_command not in valid_changes:
            change_command = input(
                "Would you like to change anything, or is this OK? (name, notes, date, ok): "
            ).lower() # Case is not important, discard it
        
        if change_command == 'name':
            # Change the name of the task.
            task_name = input("Enter new task name: ")

        elif change_command == 'notes':
            # Change the notes on the task.
            task_body = input("Enter new task notes: ")

        elif change_command == 'date':
            # Change the date on the task.
            task_due_date = None
            while task_due_date is None:
                add_due_date = input(
                    "Does this task have a deadline? (Y/N): "
                ).lower() # Case is not important, discard it
                if add_due_date == 'y':
                    task_due_date = get_datetime_from_user()
                elif add_due_date == 'n':
                    task_due_date = never_due
                    
        elif change_command == 'ok':
            # User is OK with the task, end the loop and add it to the database
            task_ok = True
    
    # All information entered and confirmed by the user, add it to the database.
    cursor.execute(
        "INSERT INTO todo (task_title, task_body, task_due) VALUES (?, ?, ?)",
        (task_name, task_body, task_due_date)
    )           

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
        # this doesn't exist yet, but will be seperated into a package
        # import usw_todo_gui
        logging.debug("The GUI is stubbed, the CLI will be called instead")
        main_cli(db_connection)
    except ModuleNotFoundError:
        main_cli(db_connection)