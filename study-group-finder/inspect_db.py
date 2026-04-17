import sqlite3
con = sqlite3.connect("instance/app.db")
cur = con.cursor()
print("study_group:")
for col in cur.execute("PRAGMA table_info(study_group)").fetchall():
    print(col)
print("group_member:")
for col in cur.execute("PRAGMA table_info(group_member)").fetchall():
    print(col)
print("group_session exists:")
print(cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='group_session'").fetchall())
con.close()
