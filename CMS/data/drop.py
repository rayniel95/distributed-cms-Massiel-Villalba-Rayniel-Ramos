import sqlite3

conn = sqlite3.connect("db.sqlite3")
cursor = conn.cursor()
cursor.execute("drop table if exists widget")
cursor.execute("drop table if exists page")

conn.commit()
conn.close()