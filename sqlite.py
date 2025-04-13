import sqlite3

# Connect to the database (or create it if it doesn't exist)
conn = sqlite3.connect('instance/site.db')

# Create a cursor object
cursor = conn.cursor()
cursor.execute("DELETE FROM shift")
#cursor.execute("INSERT INTO shift (name,start_time,end_time) VALUES (?,?, ?)", ('mornames','08.00.00','15.00.00'))
shift = [('morning', '08:00:00','16:00:00'), ('evening', '16:00:00','12:00:00'), ('nighting', '12:00:00','08:00:00')]
cursor.executemany("INSERT INTO shift (name,start_time,end_time) VALUES (?,?, ?)", shift)

conn.commit()
conn.close()