import sqlite3
import datetime
import logging

# Enable for development, will be disabled in "final version"
# logging.basicConfig(level=logging.DEBUG)

# Filename for the To Do database
todo_database_filename = "todo.db"

# A timestamp for a task that will never be due.
# (SQL "timestamp" fields MUST contain a date and time.)
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
    db_cursor.close()
    return db_connection

def display_tasks(task_list: list):
    """
    Print a list of tasks to the screen.
    
    WARNING! This is NOT view_tasks.
    This is designed to use the result of a SELECT from the Todo table
    to print the list of tasks in a nice way for the user.
    Passing arbitrary lists to this function will cause undefined behaviour!
    This code will be used multiple times, so it has been broken out into a 
    separate function.
    """        
    for task in task_list:
        id, title, _, due = task
        if datetime.datetime.fromisoformat(due) != never_due:
            print(f"{id}: '{title}', due by {due}")
        else:
            print(f"{id}: '{title}'")

def view_task(task: list):
    """
    Print a single task to the screen.
    Only designed for use with a row of the Todo table.
    Returns nothing.
    """
    id, title, body, due = task
    print()
    print(f"Task title: '{title}'")
    print(f"Task notes: {body}")
    if datetime.datetime.fromisoformat(due) != never_due:
        print(f"This task is due on: {due}")
    print()

def view_tasks(db_connection: sqlite3.Connection):
    """Present a command-line interface for viewing tasks."""

    cursor = db_connection.cursor()
    tasks = cursor.execute("SELECT * FROM todo").fetchall()
    
    if len(tasks) == 0:
        print("You have no tasks. Why not ADD one?")
        return
    
    done = False
    while done == False:
        print(f"You have {len(tasks)} tasks to do:")
        display_tasks(tasks)
        next_command = input(
            "Would you like to VIEW more info on a task, FILTER the tasks by name, change the SORT of the tasks, or are you DONE?: "
        ).lower() # case can be discarded
        if next_command == "view":
            task_id = None
            while task_id is None:
                try:
                    task_id = int(input("Enter the ID of the task you would like to view: "))
                except:
                    print("Sorry, please enter that again.")
            
            task = cursor.execute(
                "SELECT * FROM todo WHERE task_id=?;",
                (task_id,)
            ).fetchall()

            if len(task) == 0:
                print("Hmm, there's no task with that ID. Please try again.")
            else:
                view_task(task[0])
                
            
        elif next_command == "filter":
            filter_text = input("Please enter the text you would like to filter by (enter nothing to show all tasks): ")

            # Wildcards (%) are added to the string to make it a loose search.
            # This will match any name that contains the filter_text,
            # not just names that are exactly filter_text.
            tasks = cursor.execute(
                "SELECT * FROM todo WHERE task_title LIKE ?", 
                (f"%{filter_text}%",)
            ).fetchall()
        elif next_command == "sort":
            sort_type = None
            
            valid_sort_types = ("name", "id", "date")
            while sort_type not in valid_sort_types:
                sort_type = input("Would you like to sort by ID (default), NAME, or DATE?: ").lower()
            
            if sort_type == "id":
                # Sort by the first element in the task (the ID).
                tasks.sort(key=lambda x: x[0])
            elif sort_type == "name":
                # Sort by the second element in the task (the name).
                tasks.sort(key=lambda x: x[1])
            elif sort_type == "date":
                # Sort by the third element in the task (the date).
                tasks.sort(
                    key=lambda x: datetime.datetime.fromisoformat(x[3])
                )

        elif next_command == "done":
            # User is done looking at tasks, exit.
            done = True
    
    cursor.close()
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
    db_connection.commit()
    cursor.close()
    
    return

def delete_task(db_connection: sqlite3.Connection):
    """Delete a task from the database."""

    cursor = db_connection.cursor()
    tasks = cursor.execute("SELECT * FROM todo").fetchall()
    
    if len(tasks) == 0:
        print("You have no tasks to delete.")
        return
    
    print("The following tasks can be deleted:")
    display_tasks(tasks)

    task_id = None
    while task_id == None:
        try:
            task_id = int(input("Enter the ID of the task to delete: "))
        except:
            print("Sorry, try again.")
    
    safety = input(
        "Are you SURE you want to delete task {task_id}? This CANNOT be undone! (Y/N): "
    ).lower()

    if safety == 'y':
        cursor.execute(
            "DELETE FROM todo WHERE task_id=?",
            (task_id,)
        )
        db_connection.commit()
        print("The task has been deleted.")
    elif safety == 'n':
        print("Cancelled.")
    else:
        print("Ambiguous input, cancelled.")

    cursor.close()
    return

def update_task(db_connection: sqlite3.Connection):
    """Update a task in the database."""

    cursor = db_connection.cursor()
    tasks = cursor.execute("SELECT * FROM todo").fetchall()
    
    if len(tasks) == 0:
        print("You have no tasks to update.")
        return
    
    print("The following tasks can be updated:")
    display_tasks(tasks)

    task_id = None
    while task_id == None:
        try:
            task_id = int(input("Enter the ID of the task to modify: "))
        except:
            print("Sorry, try again.")

    task = cursor.execute(
        "SELECT * FROM todo WHERE task_id=?;",
        (task_id,)
    ).fetchall()

    if len(task) == 0:
        print("Hmm, there's no task with that ID. Please try again.")
    else:
        # hacky but i have 1hr30 at this point if it works ship it
        task = list(task[0])

    next_command = None
    while next_command != 'cancel':
        view_task(task)
        next_command = input(
            "Would you like to change the TITLE, NOTES or DATE, are you DONE, or would you ilke to CANCEL?: "
        ).lower()
        if next_command == 'title':
            task[1] = input("Please enter the new title:")
        elif next_command == 'notes':
            task[2] = input("Please enter the new notes:")
        elif next_command == 'date':
            task[3] = get_datetime_from_user().isoformat()
        elif next_command == 'done':
            cursor.execute(
                "UPDATE todo SET task_title=?, task_body=?,task_due=? WHERE task_id=?",
                (task[1], task[2], task[3], task[0])
            )
            db_connection.commit()
            break

    cursor.close()
    return

def main_cli(db_connection: sqlite3.Connection):
    """The main function for the CLI."""

    # Check to see if the user has any tasks due soon that they should be
    # reminded of.
    tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
    logging.debug(f"tomorrow is {tomorrow.isoformat()}")
    logging.debug(f"hunch: {len(str(tomorrow))}")

    cursor = db_connection.cursor()

    # There is a comma after the "isoformat" function to explicitly designate
    # everything between the brackets as a tuple. Without it, the SQLite module
    # attempts to interpret the string as a list of characters, and the code
    # does not work. (I am not a fan of this but understand the logic)
    cursor.execute(
        "SELECT * FROM todo WHERE task_due <= ?;",
        (tomorrow.isoformat(),)
    )
    tasks_due_soon = cursor.fetchall()
    cursor.close()

    if len(tasks_due_soon) > 0:
        print("IMPORTANT: You have tasks due soon.")
        display_tasks(tasks_due_soon)

    # Define valid commands for the CLI.
    valid_commands = ('view', 'add', 'exit')
    command = None
    while command != 'exit':
        # Print possible commands and ask what the user would like to do
        print("""
            USW To-Do
            You can:
            - VIEW a task
            - ADD a task
            - DELETE a task
            - MODIFY a task
            - EXIT from the program
        """)

        command = input("Enter a command: ").lower()
        if command == 'view':
            view_tasks(db_connection)
        elif command == 'add':
            add_task(db_connection)
        elif command == 'delete':
            delete_task(db_connection)
        elif command == 'modify':
            update_task(db_connection)
    
    # User has chosen to exit, so the loop has been exited.
    return


def main_gui(db_connection: sqlite3.Connection):
    """The main function for the Tk-based GUI."""
    print("Stubbed, calling CLI")
    main_cli(db_connection)

if __name__ == "__main__":
    db_connection = initialise_db(todo_database_filename)
    main_cli(db_connection)
    db_connection.close()