import sqlite3

# Connect to the database
conn = sqlite3.connect('instance/site.db')
cursor = conn.cursor()

# Query the task table
cursor.execute("SELECT id, content, status FROM task")
tasks = cursor.fetchall()

# Print the results
if tasks:
    print("Task Status Report:")
    print("------------------")
    for task in tasks:
        print(f"Task ID: {task[0]}")
        print(f"Content: {task[1]}")
        print(f"Status: {'Complete' if task[2] == 'complete' else 'Incomplete'}")
        print("------------------")
else:
    print("No tasks found in the database")

# Close the connection
conn.close()
