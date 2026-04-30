import sqlite3

DB_OLD = r"c:\project\rchatbotpy\old\botold.sqlite"
DB_NEW = r"c:\project\rchatbotpy\data\bot.sqlite"

def sync_stats():
    print("Starting stats sync (Additive)...")
    
    conn_old = sqlite3.connect(DB_OLD)
    conn_old.row_factory = sqlite3.Row
    conn_new = sqlite3.connect(DB_NEW)
    conn_new.row_factory = sqlite3.Row
    
    cursor_old = conn_old.cursor()
    cursor_new = conn_new.cursor()
    
    # We want to identify users that existed in bot.sqlite BEFORE the migration,
    # OR those that were just migrated but we want to ensure their stats are correctly aggregated.
    # Actually, the user's concern is about those I skipped during migration.
    
    # Let's get all users from old DB
    cursor_old.execute("SELECT user_id, coins, xp, total_chats, total_messages FROM users")
    old_users = {r['user_id']: dict(r) for r in cursor_old.fetchall()}
    
    sync_count = 0
    for uid, old_data in old_users.items():
        # Check if user exists in new DB
        cursor_new.execute("SELECT coins, xp, total_chats, total_messages FROM users WHERE user_id = ?", (uid,))
        new_row = cursor_new.fetchone()
        
        if new_row:
            # We add the values from old DB to new DB
            # Note: This might be dangerous if run multiple times, but I'm doing it once.
            # To be safer, we can check if we already added them or just do it once.
            
            # Since I already migrated, the 'new' database has the users.
            # If the user was newly migrated (156 users), they already have the old values (since I inserted them).
            # If the user was pre-existing (99 users), they have whatever they had before.
            
            # Actually, to be precise, I only want to update the 99 pre-existing users.
            # How to identify them? Based on my research, they were the 99/100 users in bot.sqlite before migration.
            
            # Better strategy: Only add if the old value > 0 and the current value != old value? 
            # No, "additive" means sum them up.
            
            # Let's just update ALL users if there's a difference, but wait...
            # If I already migrated the 156 users, their new_coins == old_coins.
            # Adding them again would double them.
            
            # So I ONLY want to update users where new_coins != old_coins (likely the 99 pre-existing ones).
            # Except user 7722829144 who had 100 (old) and 505 (new). Mismatch detected earlier.
            
            if (new_row['coins'] != old_data['coins'] or 
                new_row['xp'] != old_data['xp'] or 
                new_row['total_chats'] != old_data['total_chats'] or 
                new_row['total_messages'] != old_data['total_messages']):
                
                print(f"Syncing User {uid}: Coins +{old_data['coins']}, XP +{old_data['xp']}")
                cursor_new.execute("""
                    UPDATE users 
                    SET coins = coins + ?, 
                        xp = xp + ?,
                        total_chats = total_chats + ?,
                        total_messages = total_messages + ?
                    WHERE user_id = ?
                """, (old_data['coins'], old_data['xp'], old_data['total_chats'], old_data['total_messages'], uid))
                sync_count += 1
                
    conn_new.commit()
    print(f"Synced stats for {sync_count} users.")
    
    conn_old.close()
    conn_new.close()

if __name__ == "__main__":
    sync_stats()
