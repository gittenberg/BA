import sqlite3
from os.path import join

path = "C:\Users\MJS\gitprojects_2\BA\code\src"
con = sqlite3.connect(join(path, 'example.db'))

persons = [
    ("Hugo", "Boss"),
    ("Calvin", "Klein")
    ]

# Create the table
con.execute('''DROP TABLE IF EXISTS stocks''')
con.execute('''DROP TABLE IF EXISTS person''')
con.execute("create table person(firstname, lastname)")

# Fill the table
con.executemany("insert into person(firstname, lastname) values (?, ?)", persons)

# Print the table contents
for row in con.execute("select firstname, lastname from person"):
    print row

# Using a dummy WHERE clause to not let SQLite take the shortcut table deletes.
#print "I just deleted", con.execute("delete from person where 1=1").rowcount, "rows"

con.commit()
con.close()
