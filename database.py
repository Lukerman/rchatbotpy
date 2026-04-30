import sqlite3
import os
import time
from config import DB_PATH, QUEUE_TIMEOUT

class Database:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._init_db()
        return cls._instance

    def _init_db(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute('PRAGMA journal_mode=WAL')
        self.conn.execute('PRAGMA foreign_keys=ON')
        self.conn.execute('PRAGMA synchronous=NORMAL')
        self._init_schema()

    def _init_schema(self):
        # We assume the schema already exists since we are migrating from the PHP bot.
        # But we provide the create logic to ensure a safe initialization.
        cursor = self.conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT DEFAULT '',
                first_name TEXT DEFAULT '',
                last_name TEXT DEFAULT '',
                gender TEXT DEFAULT '',
                age INTEGER DEFAULT 0,
                interests TEXT DEFAULT '',
                language TEXT DEFAULT 'en',
                gender_pref TEXT DEFAULT 'any',
                is_banned INTEGER DEFAULT 0,
                is_vip INTEGER DEFAULT 0,
                ban_reason TEXT DEFAULT '',
                total_chats INTEGER DEFAULT 0,
                total_messages INTEGER DEFAULT 0,
                rating_sum INTEGER DEFAULT 0,
                rating_count INTEGER DEFAULT 0,
                last_active INTEGER DEFAULT 0,
                last_partner_id INTEGER DEFAULT 0,
                flood_count INTEGER DEFAULT 0,
                flood_window_start INTEGER DEFAULT 0,
                coins INTEGER DEFAULT 0,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                referral_code TEXT DEFAULT '',
                referred_by INTEGER DEFAULT 0,
                last_daily_reward INTEGER DEFAULT 0,
                daily_streak INTEGER DEFAULT 0,
                daily_chats_count INTEGER DEFAULT 0,
                daily_messages_count INTEGER DEFAULT 0,
                last_mission_reset INTEGER DEFAULT 0,
                created_at INTEGER DEFAULT 0,
                updated_at INTEGER DEFAULT 0,
                city TEXT DEFAULT '',
                match_region TEXT DEFAULT 'global',
                media_ban_until INTEGER DEFAULT 0,
                referral_reward_paid INTEGER DEFAULT 0,
                referral_cash REAL DEFAULT 0.0
            );
            
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,
                status TEXT DEFAULT 'active',
                started_at INTEGER DEFAULT 0,
                ended_at INTEGER DEFAULT 0,
                ended_by INTEGER DEFAULT 0,
                user1_rated INTEGER DEFAULT 0,
                user2_rated INTEGER DEFAULT 0,
                is_ai INTEGER DEFAULT 0,
                FOREIGN KEY (user1_id) REFERENCES users(user_id),
                FOREIGN KEY (user2_id) REFERENCES users(user_id)
            );
            
            CREATE TABLE IF NOT EXISTS queue (
                user_id INTEGER PRIMARY KEY,
                gender_pref TEXT DEFAULT 'any',
                joined_at INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
            
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                sender_id INTEGER NOT NULL,
                message_type TEXT DEFAULT 'text',
                content TEXT DEFAULT '',
                telegram_message_id INTEGER DEFAULT 0,
                created_at INTEGER DEFAULT 0,
                FOREIGN KEY (chat_id) REFERENCES chats(id),
                FOREIGN KEY (sender_id) REFERENCES users(user_id)
            );
            
            CREATE TABLE IF NOT EXISTS wall_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                likes INTEGER DEFAULT 0,
                reports INTEGER DEFAULT 0,
                created_at INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
            
            CREATE TABLE IF NOT EXISTS wall_likes (
                user_id INTEGER NOT NULL,
                post_id INTEGER NOT NULL,
                PRIMARY KEY (user_id, post_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (post_id) REFERENCES wall_posts(id)
            );
            
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reporter_id INTEGER NOT NULL,
                reported_id INTEGER NOT NULL,
                chat_id INTEGER DEFAULT 0,
                reason TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                created_at INTEGER DEFAULT 0,
                FOREIGN KEY (reporter_id) REFERENCES users(user_id),
                FOREIGN KEY (reported_id) REFERENCES users(user_id)
            );
            
            CREATE TABLE IF NOT EXISTS blocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                blocker_id INTEGER NOT NULL,
                blocked_id INTEGER NOT NULL,
                created_at INTEGER DEFAULT 0,
                FOREIGN KEY (blocker_id) REFERENCES users(user_id),
                FOREIGN KEY (blocked_id) REFERENCES users(user_id)
            );
            
            CREATE TABLE IF NOT EXISTS media_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reporter_id INTEGER NOT NULL,
                sender_id INTEGER NOT NULL,
                created_at INTEGER DEFAULT 0,
                UNIQUE(reporter_id, sender_id)
            );
            
            CREATE TABLE IF NOT EXISTS wall_post_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reporter_id INTEGER NOT NULL,
                post_id INTEGER NOT NULL,
                created_at INTEGER DEFAULT 0,
                UNIQUE(reporter_id, post_id)
            );
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT DEFAULT ''
            );
            
            CREATE TABLE IF NOT EXISTS broadcasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER NOT NULL,
                message TEXT DEFAULT '',
                sent_count INTEGER DEFAULT 0,
                created_at INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS scheduled_broadcasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER NOT NULL,
                message TEXT DEFAULT '',
                send_at INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS user_achievements (
                user_id INTEGER NOT NULL,
                achievement_type TEXT NOT NULL,
                earned_at INTEGER NOT NULL,
                PRIMARY KEY (user_id, achievement_type),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS saved_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                sender_id INTEGER NOT NULL,
                message_type TEXT DEFAULT 'text',
                content TEXT DEFAULT '',
                created_at INTEGER DEFAULT 0,
                originally_sent_at INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
            
            CREATE TABLE IF NOT EXISTS reconnect_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                requester_id INTEGER NOT NULL,
                target_id INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at INTEGER DEFAULT 0
            );
            
            CREATE TABLE IF NOT EXISTS promo_codes (
                code TEXT PRIMARY KEY,
                type TEXT DEFAULT 'coins',
                amount INTEGER DEFAULT 0,
                max_uses INTEGER DEFAULT 1,
                current_uses INTEGER DEFAULT 0,
                created_at INTEGER DEFAULT 0
            );
            
            CREATE TABLE IF NOT EXISTS promo_usage (
                user_id INTEGER NOT NULL,
                code TEXT NOT NULL,
                created_at INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, code)
            );
            
            CREATE INDEX IF NOT EXISTS idx_chats_user1 ON chats(user1_id);
            CREATE INDEX IF NOT EXISTS idx_chats_user2 ON chats(user2_id);
            CREATE INDEX IF NOT EXISTS idx_chats_status ON chats(status);
            CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_id);
            CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);
            CREATE INDEX IF NOT EXISTS idx_queue_joined ON queue(joined_at);
        """)

        # Column Migration
        try: cursor.execute("ALTER TABLE users ADD COLUMN latitude REAL DEFAULT 0.0")
        except: pass
        try: cursor.execute("ALTER TABLE users ADD COLUMN longitude REAL DEFAULT 0.0")
        except: pass
        try: cursor.execute("ALTER TABLE users ADD COLUMN country TEXT DEFAULT ''")
        except: pass
        try: cursor.execute("ALTER TABLE users ADD COLUMN city TEXT DEFAULT ''")
        except: pass
        try: cursor.execute("ALTER TABLE users ADD COLUMN media_ban_until INTEGER DEFAULT 0")
        except: pass
        try: cursor.execute("ALTER TABLE users ADD COLUMN daily_streak INTEGER DEFAULT 0")
        except: pass
        try: cursor.execute("ALTER TABLE chats ADD COLUMN is_ai INTEGER DEFAULT 0")
        except: pass
        try: cursor.execute("ALTER TABLE wall_posts ADD COLUMN reports INTEGER DEFAULT 0")
        except: pass
        try: cursor.execute("ALTER TABLE users ADD COLUMN referral_reward_paid INTEGER DEFAULT 0")
        except: pass
        try: cursor.execute("ALTER TABLE users ADD COLUMN referral_cash REAL DEFAULT 0.0")
        except: pass
        
        self.conn.commit()
        
        defaults = {
            'bot_active': '1',
            'maintenance_message': 'Bot is under maintenance. Please try again later.',
            'welcome_extra': '',
            'min_age': '13',
            'max_queue_time': '300',
            'ai_provider': 'openrouter',
            'openrouter_api_key': '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',
            'dashscope_api_key': '',
            'ai_model': 'meta-llama/llama-3.2-3b-instruct:free',
            'ai_search_delay': '3',
            'ai_system_prompt': 'You are a casual user on a random chat app. Be informal, keep it short, and never mention you are an AI.'
        }
        for k, v in defaults.items():
            cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))
            
        self.conn.commit()

        # Ensure AI User exists
        from config import AI_USER_ID
        cursor.execute("INSERT OR IGNORE INTO users (user_id, first_name, gender, gender_pref, is_vip, created_at) VALUES (?, ?, ?, ?, ?, ?)", 
                      (AI_USER_ID, "AI Partner", "any", "any", 1, int(time.time())))
        self.conn.commit()

    # ==================== SETTINGS METHODS ====================
    def get_setting(self, key, default=None):
        """Returns a single setting value."""
        c = self.conn.cursor()
        c.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = c.fetchone()
        return row['value'] if row else default

    def get_all_settings(self):
        """Returns all key-value pairs from settings table as a dictionary."""
        c = self.conn.cursor()
        c.execute("SELECT * FROM settings ORDER BY key ASC")
        return {row['key']: row['value'] for row in c.fetchall()}

    def update_setting(self, key, value):
        """Updates or inserts a setting."""
        c = self.conn.cursor()
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
        self.conn.commit()
        return True

    def set_setting(self, key, value):
        """Alias for update_setting."""
        return self.update_setting(key, value)

    # ==================== REPORT METHODS ====================
    def get_reports(self, status='pending', limit=20, offset=0):
        c = self.conn.cursor()
        c.execute("""
            SELECT r.*, 
                   u1.first_name as reporter_name, 
                   u2.first_name as reported_name
            FROM reports r
            JOIN users u1 ON r.reporter_id = u1.user_id
            JOIN users u2 ON r.reported_id = u2.user_id
            WHERE r.status = ?
            ORDER BY r.created_at DESC
            LIMIT ? OFFSET ?
        """, (status, limit, offset))
        return [dict(row) for row in c.fetchall()]

    def get_report_count(self, status='pending'):
        c = self.conn.cursor()
        c.execute("SELECT COUNT(*) as c FROM reports WHERE status = ?", (status,))
        return c.fetchone()['c']

    def resolve_report(self, report_id, new_status='resolved'):
        c = self.conn.cursor()
        c.execute("UPDATE reports SET status = ? WHERE id = ?", (new_status, report_id))
        self.conn.commit()
        return True

    # ==================== USER METHODS ====================
    def get_user_count(self):
        """Returns total number of users."""
        c = self.conn.cursor()
        c.execute("SELECT COUNT(*) as cnt FROM users")
        return c.fetchone()['cnt']

    def get_user(self, user_id):
        c = self.conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        return dict(row) if row else None

    def get_user_detailed(self, user_id):
        """Returns extra info for admin view."""
        user = self.get_user(user_id)
        if not user: return None
        
        # Add formatted date
        import datetime
        dt = datetime.datetime.fromtimestamp(user.get('created_at', 0))
        user['joined_date'] = dt.strftime('%Y-%m-%d %H:%M')
        
        # Add rating avg
        count = user.get('rating_count', 0)
        sum_val = user.get('rating_sum', 0)
        user['rating_avg'] = round(sum_val / count, 1) if count > 0 else 5.0
        
        return user
        
    def get_global_stats(self):
        """Returns (total_users, active_chats, queue_size)"""
        c = self.conn.cursor()
        c.execute("SELECT COUNT(*) FROM users")
        total_users = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM chats WHERE status = 'active'")
        active_chats = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM queue")
        queue_size = c.fetchone()[0]
        
        return total_users, active_chats, queue_size

    def get_wall_post_count(self):
        """Returns total number of global feed posts."""
        c = self.conn.cursor()
        c.execute("SELECT COUNT(*) FROM wall_posts")
        return c.fetchone()[0]

    def is_media_banned(self, user_id):
        """Checks if a user is currently under a media sending ban."""
        user = self.get_user(user_id)
        if not user: return False
        return int(time.time()) < user.get('media_ban_until', 0)
        
    def create_user(self, user_id, username, first_name, last_name='', referred_code=None):
        c = self.conn.cursor()
        now = int(time.time())
        import hashlib
        import uuid
        ref = 'ref_' + hashlib.md5(f"{user_id}{uuid.uuid4()}".encode()).hexdigest()[:8]
        try:
            # Check if user already exists
            c.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
            if c.fetchone():
                return self.get_user(user_id)
                
            c.execute("""
                INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, referral_code, created_at, updated_at, last_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, username, first_name, last_name, ref, now, now, now))
            
            # Handle referral
            if referred_code:
                c.execute("SELECT user_id FROM users WHERE referral_code = ?", (referred_code,))
                referrer = c.fetchone()
                if referrer and referrer['user_id'] != user_id:
                    referrer_id = referrer['user_id']
                    # Reward referee immediately upon joining
                    c.execute("UPDATE users SET coins = coins + 20, referred_by = ? WHERE user_id = ?", (referrer_id, user_id))
                    
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"DB Error create_user: {e}")
        return self.get_user(user_id)
        
    def get_global_stats(self):
        c = self.conn.cursor()
        c.execute("SELECT COUNT(*) as u FROM users")
        users = c.fetchone()['u']
        c.execute("SELECT COUNT(*) as a FROM chats WHERE status = 'active'")
        active = c.fetchone()['a']
        c.execute("SELECT COUNT(*) as q FROM queue")
        queue = c.fetchone()['q']
        return users, active, queue
        
    def get_referral_stats(self, user_id):
        c = self.conn.cursor()
        c.execute("SELECT COUNT(*) as ref_count FROM users WHERE referred_by = ? AND referral_reward_paid = 1", (user_id,))
        count = c.fetchone()['ref_count']
        earnings = count * 100
        cash_earnings = count * 0.001
        return count, earnings, cash_earnings
        
    def process_referral_reward(self, user_id):
        # Called when referee sends their first message
        user = self.get_user(user_id)
        if not user or not user.get('referred_by') or user.get('referral_reward_paid'):
            return None
            
        referrer_id = user['referred_by']
        c = self.conn.cursor()
        # Mark as paid for this user
        c.execute("UPDATE users SET referral_reward_paid = 1 WHERE user_id = ?", (user_id,))
        # Give reward to referrer
        c.execute("UPDATE users SET coins = coins + 100, referral_cash = referral_cash + 0.001 WHERE user_id = ?", (referrer_id,))
        self.conn.commit()
        return referrer_id
        
    # ==================== FEED METHODS ====================
    def add_wall_post(self, user_id, content):
        c = self.conn.cursor()
        now = int(time.time())
        c.execute("INSERT INTO wall_posts (user_id, content, created_at) VALUES (?, ?, ?)", (user_id, content, now))
        self.conn.commit()
        return c.lastrowid
        
    def get_wall_posts(self, offset=0, limit=1, mode='trending', viewer_id=0):
        c = self.conn.cursor()
        now = int(time.time())
        
        # Base Query
        # Score for Trending: (Likes * 10) / (Hours_Old + 1)^1.2 + (VIP_Bonus: 50)
        # We also minus reports (though they are already auto-deleted at 3, we prefer lower report counts first)
        
        viewer = self.get_user(viewer_id) if viewer_id else None
        viewer_city = viewer.get('city') if viewer else ''
        viewer_country = viewer.get('country') if viewer else ''
        
        if mode == 'new':
            order_by = "p.id DESC"
            where_clause = "1=1"
        elif mode == 'nearby' and viewer:
            order_by = "p.id DESC"
            # Prioritize same city, then same country
            where_clause = f"(u.city = '{viewer_city}' OR u.country = '{viewer_country}')"
        else: # trending
            # SQLite doesn't have POW, but we can approximate or use basic math
            # Rank = (Likes * 10) + (is_vip * 50) - (Reports * 20) + (100 / (Hours_Old + 1))
            order_by = "((p.likes * 10) + (u.is_vip * 50) - (p.reports * 20) + (360000.0 / (? - p.created_at + 3600))) DESC"
            where_clause = "1=1"

        sql = f"""
            SELECT p.id, p.user_id, p.content, p.likes, p.created_at, p.reports,
                   u.gender, u.is_vip, u.city, u.country
            FROM wall_posts p 
            JOIN users u ON p.user_id = u.user_id 
            WHERE {where_clause}
            ORDER BY {order_by}
            LIMIT ? OFFSET ?
        """
        
        if mode == 'trending':
            c.execute(sql, (now, limit, offset))
        else:
            c.execute(sql, (limit, offset))
            
        return [dict(row) for row in c.fetchall()]
        
    def get_wall_post_count(self):
        c = self.conn.cursor()
        c.execute("SELECT COUNT(*) as c FROM wall_posts")
        return c.fetchone()['c']
        
    def like_wall_post(self, post_id, user_id):
        c = self.conn.cursor()
        c.execute("SELECT * FROM wall_likes WHERE user_id = ? AND post_id = ?", (user_id, post_id))
        if c.fetchone():
            return False # Already liked
            
        try:
            c.execute("INSERT INTO wall_likes (user_id, post_id) VALUES (?, ?)", (user_id, post_id))
            c.execute("UPDATE wall_posts SET likes = likes + 1 WHERE id = ?", (post_id,))
            self.conn.commit()
            return True
        except sqlite3.Error:
            return False

    def delete_wall_post(self, post_id):
        c = self.conn.cursor()
        c.execute("DELETE FROM wall_likes WHERE post_id = ?", (post_id,))
        c.execute("DELETE FROM wall_post_reports WHERE post_id = ?", (post_id,))
        c.execute("DELETE FROM wall_posts WHERE id = ?", (post_id,))
        self.conn.commit()
        return True

    def report_wall_post(self, reporter_id, post_id, threshold=3):
        """
        Report a feed post. Returns:
          ('already_reported', count)  — user already reported this post
          ('auto_deleted', count)      — threshold hit, post removed
          ('reported', count)          — report recorded, not yet at threshold
        """
        c = self.conn.cursor()
        try:
            c.execute(
                "INSERT INTO wall_post_reports (reporter_id, post_id, created_at) VALUES (?, ?, ?)",
                (reporter_id, post_id, int(time.time()))
            )
            c.execute("UPDATE wall_posts SET reports = reports + 1 WHERE id = ?", (post_id,))
            self.conn.commit()
        except sqlite3.IntegrityError:
            c.execute("SELECT COUNT(*) as c FROM wall_post_reports WHERE post_id = ?", (post_id,))
            return 'already_reported', c.fetchone()['c']

        c.execute("SELECT COUNT(*) as c FROM wall_post_reports WHERE post_id = ?", (post_id,))
        count = c.fetchone()['c']

        if count >= threshold:
            self.delete_wall_post(post_id)
            return 'auto_deleted', count

        return 'reported', count

    def get_wall_post_by_id(self, post_id):
        c = self.conn.cursor()
        c.execute("SELECT * FROM wall_posts WHERE id = ?", (post_id,))
        row = c.fetchone()
        return dict(row) if row else None

    # ==================== MEDIA BAN METHODS ====================
    def is_media_banned(self, user_id):
        c = self.conn.cursor()
        c.execute("SELECT media_ban_until FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        if not row: return False
        return int(time.time()) < (row['media_ban_until'] or 0)

    def report_media(self, reporter_id, sender_id):
        """Log a media report. Returns (already_reported, new_count)."""
        c = self.conn.cursor()
        try:
            c.execute(
                "INSERT INTO media_reports (reporter_id, sender_id, created_at) VALUES (?, ?, ?)",
                (reporter_id, sender_id, int(time.time()))
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            return True, self.get_media_report_count(sender_id)  # already reported
        return False, self.get_media_report_count(sender_id)

    def get_media_report_count(self, sender_id):
        c = self.conn.cursor()
        c.execute("SELECT COUNT(*) as c FROM media_reports WHERE sender_id = ?", (sender_id,))
        return c.fetchone()['c']

    def apply_media_ban(self, user_id, days=3):
        ban_until = int(time.time()) + (days * 86400)
        c = self.conn.cursor()
        c.execute("UPDATE users SET media_ban_until = ? WHERE user_id = ?", (ban_until, user_id))
        # Reset reports so they don't stack indefinitely
        c.execute("DELETE FROM media_reports WHERE sender_id = ?", (user_id,))
        self.conn.commit()
        return ban_until
        
    def update_user(self, user_id, data: dict):
        """Standardized user update method with column filtering and timestamp."""
        if not data: return False
        
        # Primary columns for users table
        allowed = [
            'username', 'first_name', 'last_name', 'gender', 'age', 'interests', 
            'language', 'gender_pref', 'is_banned', 'is_vip', 'ban_reason', 
            'last_active', 'last_partner_id', 'coins', 'xp', 'level', 
            'referred_by', 'last_daily_reward', 'daily_streak', 'daily_chats_count', 
            'daily_messages_count', 'last_mission_reset', 'latitude', 'longitude', 
            'country', 'city', 'match_region', 'media_ban_until'
        ]
        
        sets = []
        values = []
        for k, v in data.items():
            if k in allowed:
                sets.append(f"{k} = ?")
                values.append(v)
        
        if not sets:
            return False
            
        sets.append("updated_at = ?")
        values.append(int(time.time()))
        
        # user_id for WHERE clause
        values.append(user_id)
        
        query = f"UPDATE users SET {', '.join(sets)} WHERE user_id = ?"
        c = self.conn.cursor()
        c.execute(query, tuple(values))
        self.conn.commit()
        return True

    def get_blocked_ids(self, user_id):
        c = self.conn.cursor()
        c.execute("SELECT blocked_id FROM blocks WHERE blocker_id = ?", (user_id,))
        blocks1 = [row['blocked_id'] for row in c.fetchall()]
        c.execute("SELECT blocker_id FROM blocks WHERE blocked_id = ?", (user_id,))
        blocks2 = [row['blocker_id'] for row in c.fetchall()]
        return blocks1 + blocks2
        
    def ban_user(self, user_id, reason=''):
        self.update_user(user_id, {'is_banned': 1, 'ban_reason': reason})
        self.remove_from_queue(user_id)
        chat = self.get_active_chat(user_id)
        if chat:
            self.end_chat(chat['id'], user_id)
            
    def increment_user_stats(self, user_id, field):
        allowed = ['total_chats', 'total_messages']
        if field not in allowed: return
        c = self.conn.cursor()
        c.execute(f"UPDATE users SET {field} = {field} + 1 WHERE user_id = ?", (user_id,))
        self.conn.commit()

    # ==================== QUEUE METHODS ====================
    def add_to_queue(self, user_id, gender_pref='any'):
        c = self.conn.cursor()
        c.execute("INSERT OR REPLACE INTO queue (user_id, gender_pref, joined_at) VALUES (?, ?, ?)", 
                 (user_id, gender_pref, int(time.time())))
        self.conn.commit()
        
    def remove_from_queue(self, user_id):
        c = self.conn.cursor()
        c.execute("DELETE FROM queue WHERE user_id = ?", (user_id,))
        self.conn.commit()
        
    def is_in_queue(self, user_id):
        c = self.conn.cursor()
        c.execute("SELECT 1 FROM queue WHERE user_id = ?", (user_id,))
        return bool(c.fetchone())

    def find_match(self, user_id):
        user = self.get_user(user_id)
        if not user: return None
        
        user_gender = user['gender']
        user_pref = user['gender_pref']
        
        c = self.conn.cursor()
        # Clean up old queue entries
        timeout_val = int(time.time()) - QUEUE_TIMEOUT
        c.execute("DELETE FROM queue WHERE joined_at < ?", (timeout_val,))
        self.conn.commit()
        
        blocked_ids = self.get_blocked_ids(user_id)
        blocked_clause = ''
        if blocked_ids:
            blocked_clause = f" AND q.user_id NOT IN ({','.join(map(str, blocked_ids))})"
            
    def find_match(self, user_id):
        """Finds a partner for a user based on gender preference, interests, and location."""
        user = self.get_user(user_id)
        if not user: return None
        
        user_gender = user.get('gender', '')
        user_pref = user.get('gender_pref', 'any')
        user_country = user.get('country', '')
        user_city = user.get('city', '')
        user_region_pref = user.get('match_region', 'global')
        
        c = self.conn.cursor()
        
        # Get list of users the user has blocked or has been blocked by
        blocked_ids = self.get_blocked_ids(user_id)
        blocked_clause = ""
        if blocked_ids:
            blocked_clause = f" AND q.user_id NOT IN ({','.join(map(str, blocked_ids))})"
            
        # Strategy: Multiple passes with decreasing strictness
        # Pass 1: Same City + Gender Pref
        # Pass 2: Same Country + Gender Pref
        # Pass 3: Global + Gender Pref
        
        conditions = [
            # 1. Same City
            f"u.city = ? AND u.city != ''" if user_region_pref in ['city', 'country', 'global'] and user_city else "1=1",
            # 2. Same Country
            f"u.country = ? AND u.country != ''" if user_region_pref in ['country', 'global'] and user_country else "1=1",
            # 3. Global
            "1=1"
        ]
        
        params = []
        if user_region_pref in ['city', 'country', 'global'] and user_city: params.append(user_city)
        if user_region_pref in ['country', 'global'] and user_country: params.append(user_country)

        # We'll stick to a simpler, single-query prioritized by ORDER BY for efficiency
        # This sorts VIPs first, then same city, then same country, then timejoined.
        
        location_score = ""
        loc_params = []
        if user_city:
            location_score += " + (CASE WHEN u.city = ? THEN 100 ELSE 0 END)"
            loc_params.append(user_city)
        if user_country:
            location_score += " + (CASE WHEN u.country = ? THEN 50 ELSE 0 END)"
            loc_params.append(user_country)

        location_order = ""
        if location_score:
            location_order = f"(0 {location_score}) DESC,"

        sql = f"""
            SELECT q.user_id, u.gender, u.is_vip, u.gender_pref as match_pref
            FROM queue q
            JOIN users u ON q.user_id = u.user_id
            WHERE q.user_id != ?
              AND u.is_banned = 0
              {blocked_clause}
              AND (
                  (? = 'any') OR 
                  (u.gender = ?) OR
                  (u.gender = '')
              )
              AND (
                  (u.gender_pref = 'any') OR 
                  (u.gender_pref = ?) OR
                  (? = '')
              )
            ORDER BY u.is_vip DESC, {location_order} q.joined_at ASC
            LIMIT 1
        """
        
        final_params = loc_params + [user_id, user_pref, user_pref, user_gender, user_gender]
        c.execute(sql, final_params)
        match = c.fetchone()
        return dict(match) if match else None

    # ==================== CHAT METHODS ====================
    def create_chat(self, user1_id, user2_id):
        now = int(time.time())
        c = self.conn.cursor()
        c.execute("""
            INSERT INTO chats (user1_id, user2_id, status, started_at)
            VALUES (?, ?, 'active', ?)
        """, (user1_id, user2_id, now))
        chat_id = c.lastrowid
        self.conn.commit()
        
        self.remove_from_queue(user1_id)
        self.remove_from_queue(user2_id)
        
        self.increment_user_stats(user1_id, 'total_chats')
        self.increment_user_stats(user2_id, 'total_chats')
        
        self.update_user(user1_id, {'last_partner_id': user2_id, 'last_active': now})
        self.update_user(user2_id, {'last_partner_id': user1_id, 'last_active': now})
        
        return chat_id

    def create_ai_chat(self, user_id):
        now = int(time.time())
        from config import AI_USER_ID
        c = self.conn.cursor()
        c.execute("""
            INSERT INTO chats (user1_id, user2_id, status, started_at, is_ai)
            VALUES (?, ?, 'active', ?, 1)
        """, (user_id, AI_USER_ID, now))
        chat_id = c.lastrowid
        self.conn.commit()
        
        self.remove_from_queue(user_id)
        self.increment_user_stats(user_id, 'total_chats')
        self.update_user(user_id, {'last_partner_id': AI_USER_ID, 'last_active': now})
        
        return chat_id

    def get_active_chat(self, user_id):
        c = self.conn.cursor()
        c.execute("""
            SELECT * FROM chats 
            WHERE status = 'active' 
              AND (user1_id = ? OR user2_id = ?)
            LIMIT 1
        """, (user_id, user_id))
        row = c.fetchone()
        return dict(row) if row else None

    def get_chat_by_id(self, chat_id):
        c = self.conn.cursor()
        c.execute("SELECT * FROM chats WHERE id = ? LIMIT 1", (chat_id,))
        row = c.fetchone()
        return dict(row) if row else None

    def end_chat(self, chat_id, ended_by=0):
        c = self.conn.cursor()
        now = int(time.time())
        c.execute("""
            UPDATE chats SET status = 'ended', ended_at = ?, ended_by = ?
            WHERE id = ? AND status = 'active'
        """, (now, ended_by, chat_id))
        self.conn.commit()

    def get_chat_partner(self, chat, user_id):
        if not chat: return None
        return chat['user2_id'] if chat['user1_id'] == user_id else chat['user1_id']
        
    def log_message(self, chat_id, sender_id, msg_type='text', content='', telegram_message_id=0):
        c = self.conn.cursor()
        now = int(time.time())
        c.execute("""
            INSERT INTO messages (chat_id, sender_id, message_type, content, telegram_message_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (chat_id, sender_id, msg_type, content, telegram_message_id, now))
        self.conn.commit()
        self.increment_user_stats(sender_id, 'total_messages')
        return c.lastrowid

    def get_chat_history(self, chat_id):
        """Retrieves messages for a specific chat."""
        c = self.conn.cursor()
        c.execute("SELECT * FROM messages WHERE chat_id = ? ORDER BY created_at ASC", (chat_id,))
        return [dict(row) for row in c.fetchall()]

    def get_saved_chats_list(self, limit=20, offset=0):
        """Returns a list of chats saved by users."""
        c = self.conn.cursor()
        c.execute("""
            SELECT sm.chat_id, sm.user_id, u.first_name, u.username, 
                   COUNT(*) as message_count, MAX(sm.created_at) as saved_at
            FROM saved_messages sm
            JOIN users u ON sm.user_id = u.user_id
            GROUP BY sm.chat_id, sm.user_id
            ORDER BY saved_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        return [dict(row) for row in c.fetchall()]

    def get_saved_chat_count(self):
        c = self.conn.cursor()
        c.execute("SELECT COUNT(DISTINCT chat_id) FROM saved_messages")
        return c.fetchone()[0]

    def get_saved_messages(self, chat_id, user_id):
        """Retrieves messages for a saved chat session."""
        c = self.conn.cursor()
        c.execute("""
            SELECT * FROM saved_messages 
            WHERE chat_id = ? AND user_id = ? 
            ORDER BY originally_sent_at ASC
        """, (chat_id, user_id))
        return [dict(row) for row in c.fetchall()]

    def get_active_chats_detailed(self):
        """Returns detailed info on all current active chats."""
        c = self.conn.cursor()
        c.execute("""
            SELECT c.*, 
                   u1.first_name as u1_name, u1.username as u1_user,
                   u2.first_name as u2_name, u2.username as u2_user
            FROM chats c
            JOIN users u1 ON c.user1_id = u1.user_id
            JOIN users u2 ON c.user2_id = u2.user_id
            WHERE c.status = 'active'
            ORDER BY c.started_at DESC
        """)
        return [dict(row) for row in c.fetchall()]

    def save_chat(self, user_id, chat_id, cost=50):
        """Saves a chat session permanently for a user."""
        user = self.get_user(user_id)
        if not user or user['coins'] < cost:
            return False, "Not enough coins."
            
        # Deduct coins
        self.add_coins(user_id, -cost)
        
        # Get messages
        messages = self.get_chat_history(chat_id)
        if not messages:
            return False, "No messages found in this chat."
            
        now = int(time.time())
        c = self.conn.cursor()
        for msg in messages:
            c.execute("""
                INSERT INTO saved_messages (chat_id, user_id, sender_id, message_type, content, created_at, originally_sent_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (chat_id, user_id, msg['sender_id'], msg['message_type'], msg['content'], now, msg['created_at']))
        
        self.conn.commit()
        return True, f"Successfully saved {len(messages)} messages!"

    def cleanup_user_chats(self, user_id):
        """Deletes messages for ended chats of a user that have no reports."""
        c = self.conn.cursor()
        # Find all ended chats for this user
        c.execute("""
            SELECT id FROM chats 
            WHERE (user1_id = ? OR user2_id = ?) 
              AND status = 'ended'
        """, (user_id, user_id))
        ended_chats = [row['id'] for row in c.fetchall()]
        
        for chat_id in ended_chats:
            # Check if there is a report for this chat
            c.execute("SELECT 1 FROM reports WHERE chat_id = ? LIMIT 1", (chat_id,))
            if not c.fetchone():
                # No report, safe to delete messages
                c.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
        
        self.conn.commit()
    
    def void_old_chat_messages(self, age_seconds=25):
        """Hard delete messages for ANY ended chat older than 'age_seconds' if no report exists."""
        cutoff = int(time.time()) - age_seconds
        c = self.conn.cursor()
        
        # Select ended chats that ended before the cutoff
        c.execute("""
            SELECT id FROM chats 
            WHERE status = 'ended' 
              AND ended_at < ?
        """, (cutoff,))
        ended_chats = [row['id'] for row in c.fetchall()]
        
        cleaned = 0
        for chat_id in ended_chats:
            # Skip if a report exists for this chat
            c.execute("SELECT 1 FROM reports WHERE chat_id = ? LIMIT 1", (chat_id,))
            if not c.fetchone():
                c.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
                cleaned += 1
        
        self.conn.commit()
        return cleaned

    # ==================== ECONOMY METHODS ====================
    def add_coins(self, user_id, amount):
        c = self.conn.cursor()
        c.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (amount, user_id))
        self.conn.commit()
        
    def purchase_vip(self, user_id, cost=500):
        user = self.get_user(user_id)
        if not user or user['coins'] < cost:
            return False
        
        self.add_coins(user_id, -cost)
        c = self.conn.cursor()
        c.execute("UPDATE users SET is_vip = 1 WHERE user_id = ?", (user_id,))
        self.conn.commit()
        return True
        
    def claim_daily(self, user_id):
        c = self.conn.cursor()
        now = int(time.time())
        c.execute("SELECT last_daily_reward, daily_streak FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        if not row: return False, 0
        
        last = row['last_daily_reward']
        streak = row['daily_streak'] or 0
        
        elapsed = now - last
        if elapsed < 86400: # 24 hours
            return False, 86400 - elapsed
            
        # Hard reset streak if > 48 hours
        if elapsed > 172800:
            streak = 0
            
        streak += 1
        
        # Scalar multiplier 
        # Day 1: 20
        # Day 2: 40
        # Day 3: 60
        # Day 4: 80
        # Day 5+: 100 max
        if streak == 1:
            amount = 20
        elif streak == 2:
            amount = 40
        elif streak == 3:
            amount = 60
        elif streak == 4:
            amount = 80
        else:
            amount = 100
            
        current_coins = self.get_user(user_id).get('coins', 0)
        c.execute("UPDATE users SET coins = ?, last_daily_reward = ?, daily_streak = ? WHERE user_id = ?", 
                  (current_coins + amount, now, streak, user_id))
        self.conn.commit()
        return True, (amount, streak)

    def redeem_promo(self, user_id, code):
        code = code.upper()
        c = self.conn.cursor()
        
        # 1. Check if promo exists
        c.execute("SELECT * FROM promo_codes WHERE code = ?", (code,))
        promo = c.fetchone()
        if not promo:
            return 'invalid'
            
        # 2. Check if user already used this specific code
        c.execute("SELECT 1 FROM promo_usage WHERE user_id = ? AND code = ? LIMIT 1", (user_id, code))
        if c.fetchone():
            return 'already_used'
            
        # 3. Check if global limit is reached
        c.execute("SELECT COUNT(*) as cnt FROM promo_usage WHERE code = ?", (code,))
        total_usages = c.fetchone()['cnt']
        if total_usages >= promo['max_uses']:
            return 'expired'
            
        # 4. Record usage
        now = int(time.time())
        c.execute("INSERT INTO promo_usage (user_id, code, created_at) VALUES (?, ?, ?)", (user_id, code, now))
        
        # 5. Increment current_uses in promo_codes table for the admin panel view
        c.execute("UPDATE promo_codes SET current_uses = current_uses + 1 WHERE code = ?", (code,))
        
        # 6. Apply benefits
        if promo['type'] == 'coins':
            self.add_coins(user_id, promo['amount'])
            result_data = {'type': 'coins', 'amount': promo['amount']}
        elif promo['type'] == 'vip':
            c.execute("UPDATE users SET is_vip = 1 WHERE user_id = ?", (user_id,))
            result_data = {'type': 'vip'}
        else:
            result_data = {'type': 'error'}
            
        self.conn.commit()
        return result_data

    def get_user_achievements(self, user_id):
        """Retrieves earned achievements for a user."""
        c = self.conn.cursor()
        c.execute("SELECT achievement_type, earned_at FROM user_achievements WHERE user_id = ?", (user_id,))
        return [dict(row) for row in c.fetchall()]

    def check_achievements(self, user_id):
        """Checks if user has met any new achievement milestones."""
        user = self.get_user(user_id)
        if not user: return []
        
        earned = [a['achievement_type'] for a in self.get_user_achievements(user_id)]
        new_achievements = []
        
        milestones = {
            'social_butterfly': {'field': 'total_chats', 'value': 100},
            'talkative': {'field': 'total_messages', 'value': 500},
            'coin_collector': {'field': 'coins', 'value': 1000},
            'guardian': {'field': 'rating_count', 'value': 10, 'min_rating': 4.0}, 
        }
        
        c = self.conn.cursor()
        now = int(time.time())
        
        # Simple threshold checks
        for ach_type, req in milestones.items():
            if ach_type not in earned:
                meets_val = user.get(req['field'], 0) >= req.get('value', 999999)
                meets_extra = True
                
                # Special check for guardian (Average rating)
                if ach_type == 'guardian' and meets_val:
                    avg = user.get('rating_sum', 0) / max(user.get('rating_count', 1), 1)
                    if avg < req.get('min_rating', 0):
                        meets_extra = False
                
                if meets_val and meets_extra:
                    c.execute("INSERT OR IGNORE INTO user_achievements (user_id, achievement_type, earned_at) VALUES (?, ?, ?)", (user_id, ach_type, now))
                    new_achievements.append(ach_type)
        
        # Special check: Registration age (Veteran)
        if 'veteran' not in earned:
            days_joined = (now - user.get('created_at', now)) / 86400
            if days_joined >= 30:
                c.execute("INSERT OR IGNORE INTO user_achievements (user_id, achievement_type, earned_at) VALUES (?, ?, ?)", (user_id, 'veteran', now))
                new_achievements.append('veteran')

        if new_achievements:
            self.conn.commit()
            
        return new_achievements
    # ==================== COMMUNITY & RATING METHODS ====================
    def get_top_users(self, limit=10):
        c = self.conn.cursor()
        c.execute("""
            SELECT user_id, first_name, username, xp, level, is_vip, coins 
            FROM users 
            WHERE is_banned = 0 
            ORDER BY xp DESC, level DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in c.fetchall()]

    def update_rating(self, user_id, rating):
        c = self.conn.cursor()
        c.execute("UPDATE users SET rating_sum = rating_sum + ?, rating_count = rating_count + 1 WHERE user_id = ?", (rating, user_id))
        self.conn.commit()
        

    def update_location(self, user_id, latitude, longitude, country='', city=''):
        """Updates user coordinates and optional region info."""
        self.update_user(user_id, {
            'latitude': latitude,
            'longitude': longitude,
            'country': country,
            'city': city
        })
        
    def add_xp(self, user_id, amount):
        user = self.get_user(user_id)
        if not user: return False
        
        new_xp = user['xp'] + amount
        new_level = (new_xp // 100) + 1
        
        c = self.conn.cursor()
        c.execute("UPDATE users SET xp = ?, level = ? WHERE user_id = ?", (new_xp, new_level, user_id))
        self.conn.commit()
        return new_level > user['level']
        
    def set_chat_rated(self, chat_id, user_id):
        c = self.conn.cursor()
        c.execute("SELECT user1_id FROM chats WHERE id = ?", (chat_id,))
        chat = c.fetchone()
        if not chat: return
        if chat['user1_id'] == user_id:
            c.execute("UPDATE chats SET user1_rated = 1 WHERE id = ?", (chat_id,))
        else:
            c.execute("UPDATE chats SET user2_rated = 1 WHERE id = ?", (chat_id,))
        self.conn.commit()

    def has_rated(self, chat_id, user_id):
        c = self.conn.cursor()
        c.execute("SELECT user1_id, user1_rated, user2_rated FROM chats WHERE id = ?", (chat_id,))
        chat = c.fetchone()
        if not chat: return True
        return bool(chat['user1_rated'] if chat['user1_id'] == user_id else chat['user2_rated'])

    def block_user(self, blocker_id, blocked_id):
        c = self.conn.cursor()
        now = int(time.time())
        c.execute("INSERT OR IGNORE INTO blocks (blocker_id, blocked_id, created_at) VALUES (?, ?, ?)", 
                  (blocker_id, blocked_id, now))
        self.conn.commit()

    def report_user(self, reporter_id, reported_id, chat_id, reason):
        c = self.conn.cursor()
        now = int(time.time())
        c.execute("""
            INSERT INTO reports (reporter_id, reported_id, chat_id, reason, created_at) 
            VALUES (?, ?, ?, ?, ?)
        """, (reporter_id, reported_id, chat_id, reason, now))
        
        # Check auto-ban
        c.execute("SELECT COUNT(*) as count FROM reports WHERE reported_id = ?", (reported_id,))
        report_count = c.fetchone()['count']
        
        banned = False
        from config import MAX_REPORTS_BEFORE_BAN
        if report_count >= MAX_REPORTS_BEFORE_BAN:
            self.ban_user(reported_id, reason="Auto-ban from multiple reports")
            banned = True
            
        self.conn.commit()
        return banned

    def get_user_reporters(self, user_id):
        """Returns unique Telegram IDs of users who reported this user."""
        c = self.conn.cursor()
        c.execute("SELECT DISTINCT reporter_id FROM reports WHERE reported_id = ?", (user_id,))
        return [row['reporter_id'] for row in c.fetchall()]

    def get_active_user_ids(self):
        """Returns all non-banned user IDs."""
        c = self.conn.cursor()
        c.execute("SELECT user_id FROM users WHERE is_banned = 0")
        return [row['user_id'] for row in c.fetchall()]

    def get_all_promos(self):
        """Returns all promo codes with real-time usage counts from the usage table."""
        c = self.conn.cursor()
        c.execute("""
            SELECT pc.*, 
                   (SELECT COUNT(*) FROM promo_usage pu WHERE pu.code = pc.code) as live_uses
            FROM promo_codes pc 
            ORDER BY pc.created_at DESC
        """)
        return [dict(row) for row in c.fetchall()]

    def delete_promo(self, code):
        c = self.conn.cursor()
        c.execute("DELETE FROM promo_codes WHERE code = ?", (code,))
        self.conn.commit()
        return True

    def create_promo_admin(self, code, ptype, amount, max_uses):
        c = self.conn.cursor()
        now = int(time.time())
        c.execute("""
            INSERT OR REPLACE INTO promo_codes (code, type, amount, max_uses, current_uses, created_at)
            VALUES (?, ?, ?, ?, 0, ?)
        """, (code.upper(), ptype, amount, max_uses, now))
        self.conn.commit()
        return True
