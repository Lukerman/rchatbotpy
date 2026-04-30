import sqlite3

def check_mismatches(db_old, db_new):
    conn_old = sqlite3.connect(db_old)
    conn_new = sqlite3.connect(db_new)
    conn_old.row_factory = sqlite3.Row
    conn_new.row_factory = sqlite3.Row
    
    cursor_old = conn_old.cursor()
    cursor_new = conn_new.cursor()
    
    cursor_old.execute("SELECT user_id, coins, xp, level FROM users")
    old_data = {r['user_id']: dict(r) for r in cursor_old.fetchall()}
    
    cursor_new.execute("SELECT user_id, coins, xp, level FROM users")
    new_data = {r['user_id']: dict(r) for r in cursor_new.fetchall()}
    
    mismatches = []
    for uid, old_user in old_data.items():
        if uid in new_data:
            new_user = new_data[uid]
            if old_user['coins'] != new_user['coins']:
                mismatches.append((uid, old_user['coins'], new_user['coins']))
    
    print(f"Total Mismatches Found: {len(mismatches)}")
    if mismatches:
        print("Sample Mismatches (UserID, OldCoins, NewCoins):")
        for m in mismatches[:10]:
            print(m)

    conn_old.close()
    conn_new.close()

if __name__ == "__main__":
    check_mismatches(r"c:\project\rchatbotpy\old\botold.sqlite", r"c:\project\rchatbotpy\data\bot.sqlite")
