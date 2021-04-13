import sqlite3

conn = sqlite3.connect("db.sqlite3")
cursor = conn.cursor()

# widget = (name,hash,estado,params)
cursor.execute("create table if not exists page (name text PRIMARY KEY UNIQUE, hash text, estado text,params text)")
cursor.execute("create table if not exists widget (name text PRIMARY KEY UNIQUE, hash text, estado text, params text)")

conn.commit()
conn.close()

'''
El param de las paginas es un string:
    param = section-1 * .... * section-n
    sections = header, nav, section, aside, footer
    section-k = #widget-1 params_to_1 .... #widget-n params_to_n
'''