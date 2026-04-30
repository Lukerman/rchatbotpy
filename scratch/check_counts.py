import sqlite3

def check_counts(db_path):
    print(f"--- Row Counts for {db_path} ---")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for table in tables:
        table_name = table[0]
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"Table: {table_name:20} | Count: {count}")
        except:
            pass
    conn.close()

if __name__ == "__main__":
    check_counts(r"c:\project\rchatbotpy\old\botold.sqlite")
    check_counts(r"c:\project\rchatbotpy\data\bot.sqlite")
