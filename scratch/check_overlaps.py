import sqlite3

def check_overlaps(db_old, db_new):
    conn_old = sqlite3.connect(db_old)
    conn_new = sqlite3.connect(db_new)
    
    cursor_old = conn_old.cursor()
    cursor_new = conn_new.cursor()
    
    cursor_old.execute("SELECT user_id FROM users")
    old_ids = set(r[0] for r in cursor_old.fetchall())
    
    cursor_new.execute("SELECT user_id FROM users")
    new_ids = set(r[0] for r in cursor_new.fetchall())
    
    overlaps = old_ids.intersection(new_ids)
    print(f"Total Old Users: {len(old_ids)}")
    print(f"Total New Users: {len(new_ids)}")
    print(f"Overlapping IDs: {len(overlaps)}")
    if overlaps:
        print(f"Sample Overlaps: {list(overlaps)[:5]}")
        
    conn_old.close()
    conn_new.close()

if __name__ == "__main__":
    check_overlaps(r"c:\project\rchatbotpy\old\botold.sqlite", r"c:\project\rchatbotpy\data\bot.sqlite")
