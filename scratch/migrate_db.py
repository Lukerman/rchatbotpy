import sqlite3
import os

DB_OLD = r"c:\project\rchatbotpy\old\botold.sqlite"
DB_NEW = r"c:\project\rchatbotpy\data\bot.sqlite"

def migrate():
    print("Starting migration...")
    
    conn_old = sqlite3.connect(DB_OLD)
    conn_old.row_factory = sqlite3.Row
    conn_new = sqlite3.connect(DB_NEW)
    conn_new.row_factory = sqlite3.Row
    
    cursor_old = conn_old.cursor()
    cursor_new = conn_new.cursor()
    
    # 1. Migrate Users
    print("Migrating users...")
    cursor_old.execute("SELECT * FROM users")
    rows = cursor_old.fetchall()
    user_migrated = 0
    for row in rows:
        d = dict(row)
        # Check if user exists
        cursor_new.execute("SELECT user_id FROM users WHERE user_id = ?", (d['user_id'],))
        if cursor_new.fetchone():
            continue
            
        columns = ', '.join(d.keys())
        placeholders = ', '.join(['?'] * len(d))
        sql = f"INSERT INTO users ({columns}) VALUES ({placeholders})"
        cursor_new.execute(sql, list(d.values()))
        user_migrated += 1
    conn_new.commit()
    print(f"Migrated {user_migrated} new users.")

    # 2. Migrate Chats (with ID mapping)
    print("Migrating chats...")
    cursor_old.execute("SELECT * FROM chats")
    rows = cursor_old.fetchall()
    chat_map = {} # old_id -> new_id
    chat_migrated = 0
    for row in rows:
        d = dict(row)
        old_id = d.pop('id')
        
        # Check if this chat (by users and started_at) already exists to avoid duplicates if possible
        # but usually we just append.
        columns = ', '.join(d.keys())
        placeholders = ', '.join(['?'] * len(d))
        sql = f"INSERT INTO chats ({columns}) VALUES ({placeholders})"
        cursor_new.execute(sql, list(d.values()))
        new_id = cursor_new.lastrowid
        chat_map[old_id] = new_id
        chat_migrated += 1
    conn_new.commit()
    print(f"Migrated {chat_migrated} chats.")

    # 3. Migrate Messages
    print("Migrating messages...")
    cursor_old.execute("SELECT * FROM messages")
    rows = cursor_old.fetchall()
    msg_migrated = 0
    for row in rows:
        d = dict(row)
        old_id = d.pop('id')
        old_chat_id = d['chat_id']
        
        if old_chat_id in chat_map:
            d['chat_id'] = chat_map[old_chat_id]
            columns = ', '.join(d.keys())
            placeholders = ', '.join(['?'] * len(d))
            sql = f"INSERT INTO messages ({columns}) VALUES ({placeholders})"
            cursor_new.execute(sql, list(d.values()))
            msg_migrated += 1
    conn_new.commit()
    print(f"Migrated {msg_migrated} messages.")

    # 4. Migrate Wall Posts
    print("Migrating wall posts...")
    post_map = {}
    cursor_old.execute("SELECT * FROM wall_posts")
    rows = cursor_old.fetchall()
    for row in rows:
        d = dict(row)
        old_id = d.pop('id')
        columns = ', '.join(d.keys())
        placeholders = ', '.join(['?'] * len(d))
        sql = f"INSERT INTO wall_posts ({columns}) VALUES ({placeholders})"
        cursor_new.execute(sql, list(d.values()))
        post_map[old_id] = cursor_new.lastrowid
    conn_new.commit()

    # 5. Migrate Wall Likes
    print("Migrating wall likes...")
    cursor_old.execute("SELECT * FROM wall_likes")
    rows = cursor_old.fetchall()
    for row in rows:
        d = dict(row)
        if d['post_id'] in post_map:
            d['post_id'] = post_map[d['post_id']]
            columns = ', '.join(d.keys())
            placeholders = ', '.join(['?'] * len(d))
            sql = f"INSERT OR IGNORE INTO wall_likes ({columns}) VALUES ({placeholders})"
            cursor_new.execute(sql, list(d.values()))
    conn_new.commit()

    # 6. Migrate Reports, Blocks, etc.
    print("Migrating other data...")
    tables_to_copy = ['reports', 'blocks', 'reconnect_requests', 'broadcasts']
    for table in tables_to_copy:
        cursor_old.execute(f"SELECT * FROM {table}")
        rows = cursor_old.fetchall()
        for row in rows:
            d = dict(row)
            if 'id' in d: d.pop('id')
            if 'chat_id' in d and d['chat_id'] != 0 and d['chat_id'] in chat_map:
                d['chat_id'] = chat_map[d['chat_id']]
            
            columns = ', '.join(d.keys())
            placeholders = ', '.join(['?'] * len(d))
            sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            cursor_new.execute(sql, list(d.values()))
    conn_new.commit()

    # 7. Migrate Settings (only if missing)
    print("Migrating missing settings...")
    cursor_old.execute("SELECT * FROM settings")
    rows = cursor_old.fetchall()
    for row in rows:
        cursor_new.execute("SELECT 1 FROM settings WHERE key = ?", (row['key'],))
        if not cursor_new.fetchone():
            cursor_new.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (row['key'], row['value']))
    conn_new.commit()

    print("Migration completed successfully.")
    conn_old.close()
    conn_new.close()

if __name__ == "__main__":
    migrate()
