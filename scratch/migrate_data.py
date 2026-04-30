import sqlite3
import os
import time

old_db_path = r'c:\project\rchatbotpy\old\bot (1).sqlite'
new_db_path = r'c:\project\rchatbotpy\data\bot.sqlite'

def migrate():
    if not os.path.exists(old_db_path):
        print("Old database not found.")
        return

    old_conn = sqlite3.connect(old_db_path)
    old_conn.row_factory = sqlite3.Row
    new_conn = sqlite3.connect(new_db_path)
    
    # 1. Migrate Users
    print("Migrating users...")
    old_users = old_conn.execute("SELECT * FROM users").fetchall()
    user_cols = [
        'user_id', 'username', 'first_name', 'last_name', 'gender', 'age', 'interests', 
        'language', 'gender_pref', 'is_banned', 'is_vip', 'ban_reason', 'total_chats', 
        'total_messages', 'rating_sum', 'rating_count', 'last_active', 'last_partner_id', 
        'flood_count', 'flood_window_start', 'coins', 'xp', 'level', 'referral_code', 
        'referred_by', 'last_daily_reward', 'daily_chats_count', 'daily_messages_count', 
        'last_mission_reset', 'created_at', 'updated_at'
    ]
    
    placeholders = ", ".join(["?"] * len(user_cols))
    cols_str = ", ".join(user_cols)
    
    count = 0
    for row in old_users:
        values = [row[c] for c in user_cols]
        try:
            new_conn.execute(f"INSERT OR IGNORE INTO users ({cols_str}) VALUES ({placeholders})", values)
            count += 1
        except Exception as e:
            print(f"Error migrating user {row['user_id']}: {e}")
            
    new_conn.commit()
    print(f"Migrated {count} users.")

    # 2. Migrate Wall Posts
    print("Migrating wall posts...")
    old_posts = old_conn.execute("SELECT * FROM wall_posts").fetchall()
    count = 0
    for row in old_posts:
        try:
            new_conn.execute("INSERT OR IGNORE INTO wall_posts (id, user_id, content, likes, reports, created_at) VALUES (?, ?, ?, ?, ?, ?)", 
                             (row['id'], row['user_id'], row['content'], row['likes'], row['reports'], row['created_at']))
            count += 1
        except Exception as e:
            print(f"Error migrating post {row['id']}: {e}")
    new_conn.commit()
    print(f"Migrated {count} wall posts.")

    # 3. Migrate Messages (Chat History)
    print("Migrating messages...")
    old_msgs = old_conn.execute("SELECT * FROM messages").fetchall()
    count = 0
    for row in old_msgs:
        try:
            new_conn.execute("INSERT OR IGNORE INTO messages (id, chat_id, sender_id, message_type, content, telegram_message_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                             (row['id'], row['chat_id'], row['sender_id'], row['message_type'], row['content'], row['telegram_message_id'], row['created_at']))
            count += 1
        except Exception as e:
            pass # Likely duplicate IDs or missing parent chats
    new_conn.commit()
    print(f"Migrated {count} messages.")

    # 4. Cleanup/Final
    old_conn.close()
    new_conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
