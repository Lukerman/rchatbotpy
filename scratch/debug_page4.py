import sqlite3
import os

db_path = r'c:\project\rchatbotpy\data\bot.sqlite'

def debug_users_page():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    limit = 20
    page = 4
    offset = (page - 1) * limit
    
    print(f"Fetching users for page {page} (offset {offset})...")
    c.execute("SELECT * FROM users ORDER BY last_active DESC LIMIT ? OFFSET ?", (limit, offset))
    rows = c.fetchall()
    
    print(f"Row count: {len(rows)}")
    for i, row in enumerate(rows):
        d = dict(row)
        # Check for extremely long strings
        for k, v in d.items():
            if isinstance(v, str) and len(v) > 500:
                print(f"Row {i} ({d['user_id']}) has long string in {k}: Len {len(v)}")
        
    conn.close()

if __name__ == "__main__":
    debug_users_page()
