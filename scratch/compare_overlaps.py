import sqlite3

def compare_overlaps(db_old, db_new):
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
    
    overlaps = set(old_data.keys()).intersection(new_data.keys())
    print(f"Comparing {len(overlaps)} overlaps...")
    
    diff_coins = 0
    for uid in list(overlaps)[:10]:
        o = old_data[uid]
        n = new_data[uid]
        print(f"User {uid}: Old Coins={o['coins']}, New Coins={n['coins']} | Old XP={o['xp']}, New XP={n['xp']}")
        if o['coins'] != n['coins']:
            diff_coins += 1
            
    conn_old.close()
    conn_new.close()

if __name__ == "__main__":
    compare_overlaps(r"c:\project\rchatbotpy\old\botold.sqlite", r"c:\project\rchatbotpy\data\bot.sqlite")
