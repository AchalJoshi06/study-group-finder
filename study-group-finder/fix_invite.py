import sqlite3
con = sqlite3.connect("instance/app.db")
cur = con.cursor()
try:
    cur.execute("ALTER TABLE study_group ADD COLUMN invite_token VARCHAR(32)")
    print("Added invite_token (non-unique)")
except Exception as e:
    print(f"Error: {e}")
con.commit()
con.close()
