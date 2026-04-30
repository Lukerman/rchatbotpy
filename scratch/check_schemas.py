import sqlite3

def check_schema(db_path):
    print(f"--- Schema for {db_path} ---")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for table in tables:
        table_name = table[0]
        print(f"\nTable: {table_name}")
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
    conn.close()

if __name__ == "__main__":
    check_schema(r"c:\project\rchatbotpy\old\botold.sqlite")
    check_schema(r"c:\project\rchatbotpy\data\bot.sqlite")
