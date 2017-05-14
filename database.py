import sqlite3
conn = sqlite3.connect('lawyerai.db')

c = conn.cursor()

c.execute('''CREATE TABLE sessions (json text)''')

conn.commit()

conn.close()