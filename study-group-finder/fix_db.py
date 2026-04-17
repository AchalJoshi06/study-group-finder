import sqlite3
con = sqlite3.connect("instance/app.db")
cur = con.cursor()
def run(sql, msg):
    try:
        cur.execute(sql)
        print(msg)
    except Exception as e:
        print(f"Error {msg}: {e}")

run("ALTER TABLE study_group ADD COLUMN invite_token VARCHAR(32) UNIQUE", "Added invite_token")
run("ALTER TABLE group_member ADD COLUMN role VARCHAR(20) DEFAULT 'member'", "Added role")
run("CREATE TABLE group_session (id INTEGER PRIMARY KEY, group_id INTEGER NOT NULL, start_time DATETIME NOT NULL, end_time DATETIME, topics TEXT, FOREIGN KEY(group_id) REFERENCES study_group (id))", "Created group_session")
con.commit()
con.close()
