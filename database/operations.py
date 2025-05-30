import sqlite3
# import psycopg2  # فقط برای production
try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    psycopg2 = None
import datetime
import os
import secrets
import string

def get_connection():
    """اتصال هوشمند به دیتابیس"""
    database_url = os.getenv("DATABASE_URL")
    
    if database_url and database_url.startswith("postgres"):
        # Production: PostgreSQL
        print("🐘 Connecting to PostgreSQL...")
        return psycopg2.connect(database_url)
    else:
        # Development: SQLite
        print("🗄️ Connecting to SQLite...")
        return sqlite3.connect('bot_database.db')

def init_db():
    """ایجاد پایگاه داده و جداول مورد نیاز - PostgreSQL Compatible + Referral System"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # تشخیص نوع دیتابیس
    is_postgres = hasattr(conn, 'server_version')
    
    if is_postgres:
        # PostgreSQL syntax
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                subscription_end DATE,
                subscription_type TEXT,
                is_active BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                referral_code TEXT,
                custom_commission_rate DECIMAL(5,2),
                total_earned DECIMAL(10,2) DEFAULT 0.00,
                total_paid DECIMAL(10,2) DEFAULT 0.00
            )
        ''')
        
        # اضافه کردن unique constraint برای referral_code
        try:
            cursor.execute('ALTER TABLE users ADD CONSTRAINT users_referral_code_unique UNIQUE (referral_code)')
            conn.commit()
        except Exception:
            conn.rollback()  # constraint already exists
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                txid TEXT,
                wallet_address TEXT,
                amount DECIMAL(10,2),
                subscription_type TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_requests (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                endpoint TEXT,
                request_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # جدول جدید: referrals - ردیابی روابط دعوت
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                id SERIAL PRIMARY KEY,
                referrer_id BIGINT NOT NULL,
                referred_id BIGINT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (referrer_id) REFERENCES users (user_id),
                FOREIGN KEY (referred_id) REFERENCES users (user_id),
                UNIQUE(referrer_id, referred_id)
            )
        ''')
        
        # جدول جدید: commissions - مدیریت کمیسیون‌ها
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS commissions (
                id SERIAL PRIMARY KEY,
                referrer_id BIGINT NOT NULL,
                referred_id BIGINT NOT NULL,
                transaction_id INTEGER,
                plan_type TEXT NOT NULL,
                commission_amount DECIMAL(10,2) NOT NULL,
                bonus_amount DECIMAL(10,2) DEFAULT 0.00,
                total_amount DECIMAL(10,2) NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                paid_at TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES users (user_id),
                FOREIGN KEY (referred_id) REFERENCES users (user_id),
                FOREIGN KEY (transaction_id) REFERENCES transactions (id)
            )
        ''')
        
        # جدول جدید: referral_settings - تنظیمات سیستم
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referral_settings (
                id SERIAL PRIMARY KEY,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ایجاد ایندکس‌ها برای بهتر شدن عملکرد - Safe Migration
        try:
            cursor.execute('''CREATE INDEX IF NOT EXISTS idx_users_subscription ON users(subscription_end, is_active)''')
        except Exception as e:
            print(f"Index users_subscription already exists or error: {e}")
        
        try:
            cursor.execute('''CREATE INDEX IF NOT EXISTS idx_users_referral_code ON users(referral_code)''')
        except Exception as e:
            print(f"Index users_referral_code skipped (column may not exist yet): {e}")
        
        try:
            cursor.execute('''CREATE INDEX IF NOT EXISTS idx_api_requests_date ON api_requests(user_id, request_date)''')
        except Exception as e:
            print(f"Index api_requests_date already exists or error: {e}")
        
        try:
            cursor.execute('''CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id)''')
        except Exception as e:
            print(f"Index referrals_referrer skipped (table may not exist yet): {e}")
        
        try:
            cursor.execute('''CREATE INDEX IF NOT EXISTS idx_referrals_referred ON referrals(referred_id)''')
        except Exception as e:
            print(f"Index referrals_referred skipped (table may not exist yet): {e}")
        
        try:
            cursor.execute('''CREATE INDEX IF NOT EXISTS idx_commissions_referrer ON commissions(referrer_id, status)''')
        except Exception as e:
            print(f"Index commissions_referrer skipped (table may not exist yet): {e}")
        
        try:
            cursor.execute('''CREATE INDEX IF NOT EXISTS idx_commissions_status ON commissions(status)''')
        except Exception as e:
            print(f"Index commissions_status skipped (table may not exist yet): {e}")
        
    else:
        # SQLite syntax (development)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                subscription_end DATE,
                subscription_type TEXT,
                is_active BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                referral_code TEXT UNIQUE,
                custom_commission_rate REAL,
                total_earned REAL DEFAULT 0.00,
                total_paid REAL DEFAULT 0.00
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                txid TEXT,
                wallet_address TEXT,
                amount REAL,
                subscription_type TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                endpoint TEXT,
                request_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                referred_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (referrer_id) REFERENCES users (user_id),
                FOREIGN KEY (referred_id) REFERENCES users (user_id),
                UNIQUE(referrer_id, referred_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS commissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                referred_id INTEGER NOT NULL,
                transaction_id INTEGER,
                plan_type TEXT NOT NULL,
                commission_amount REAL NOT NULL,
                bonus_amount REAL DEFAULT 0.00,
                total_amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                paid_at TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES users (user_id),
                FOREIGN KEY (referred_id) REFERENCES users (user_id),
                FOREIGN KEY (transaction_id) REFERENCES transactions (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referral_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
    # اضافه کردن default settings
    try:
        cursor.execute('''
            INSERT INTO referral_settings (setting_key, setting_value) 
            VALUES ('min_withdrawal_amount', '20.00')
            ON CONFLICT (setting_key) DO NOTHING
        ''' if is_postgres else '''
            INSERT OR IGNORE INTO referral_settings (setting_key, setting_value) 
            VALUES ('min_withdrawal_amount', '20.00')
        ''')
        conn.commit()
    except Exception as e:
        print(f"Default settings insert error: {e}")
        conn.rollback()
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")

def check_subscription(user_id):
    """بررسی وضعیت اشتراک کاربر - PostgreSQL Compatible"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT subscription_end, is_active FROM users WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return False
    
    end_date_str, is_active = result
    if not is_active or not end_date_str:
        conn.close()
        return False
    
    # تبدیل به datetime اگر string باشد
    if isinstance(end_date_str, str):
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
    else:
        end_date = end_date_str
    
    today = datetime.date.today()
    
    conn.close()
    return end_date >= today

def generate_referral_code(user_id):
    """تولید کد رفرال منحصر به فرد"""
    # ترکیب user_id با کد تصادفی
    random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    return f"REF{user_id}{random_part}"

def register_user(user_id, username):
    """ثبت کاربر جدید در دیتابیس - PostgreSQL Compatible + Referral"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # تولید کد رفرال
    referral_code = generate_referral_code(user_id)
    
    # PostgreSQL: ON CONFLICT, SQLite: INSERT OR IGNORE
    is_postgres = hasattr(conn, 'server_version')
    
    if is_postgres:
        cursor.execute("""
            INSERT INTO users (user_id, username, referral_code) 
            VALUES (%s, %s, %s) 
            ON CONFLICT (user_id) DO UPDATE SET
            username = EXCLUDED.username,
            referral_code = COALESCE(users.referral_code, EXCLUDED.referral_code)
        """, (user_id, username, referral_code))
    else:
        # برای SQLite: ابتدا چک کنیم کاربر وجود دارد یا نه
        cursor.execute("SELECT user_id, referral_code FROM users WHERE user_id = ?", (user_id,))
        existing_user = cursor.fetchone()
        
        if not existing_user:
            cursor.execute(
                "INSERT INTO users (user_id, username, referral_code) VALUES (?, ?, ?)",
                (user_id, username, referral_code)
            )
        else:
            # اگر کاربر وجود دارد اما کد رفرال ندارد، اضافه کن
            if not existing_user[1]:  # referral_code خالی است
                cursor.execute(
                    "UPDATE users SET referral_code = ?, username = ? WHERE user_id = ?",
                    (referral_code, username, user_id)
                )
    
    conn.commit()
    conn.close()
    print(f"✅ User {user_id} registered with referral code: {referral_code}")

def activate_subscription(user_id, duration_months, sub_type):
    """فعال‌سازی اشتراک کاربر - PostgreSQL Compatible"""
    conn = get_connection()
    cursor = conn.cursor()
    
    today = datetime.date.today()
    end_date = today + datetime.timedelta(days=30 * duration_months)
    
    cursor.execute("""
        UPDATE users 
        SET subscription_end = %s, subscription_type = %s, is_active = %s 
        WHERE user_id = %s
    """, (end_date, sub_type, True, user_id))
    
    conn.commit()
    conn.close()
    return end_date.strftime('%Y-%m-%d')

def get_user_info(user_id):
    """دریافت اطلاعات کاربر - PostgreSQL Compatible"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user_data = cursor.fetchone()
    
    if not user_data:
        conn.close()
        return None
    
    # دریافت تراکنش‌های اخیر کاربر
    cursor.execute("""
        SELECT * FROM transactions 
        WHERE user_id = %s 
        ORDER BY created_at DESC 
        LIMIT 5
    """, (user_id,))
    transactions = cursor.fetchall()
    
    conn.close()
    return {"user_data": user_data, "transactions": transactions}

def save_transaction(user_id, txid, wallet_address, amount, subscription_type):
    """ذخیره تراکنش جدید - PostgreSQL Compatible"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO transactions (user_id, txid, wallet_address, amount, subscription_type) 
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, txid, wallet_address, amount, subscription_type))
    
    conn.commit()
    conn.close()

def check_user_api_limit(user_id, is_premium=False):
    """بررسی محدودیت درخواست API کاربر - PostgreSQL Compatible"""
    conn = get_connection()
    cursor = conn.cursor()
    
    today = datetime.date.today()
    
    # شمارش درخواست‌های امروز
    cursor.execute("""
        SELECT COUNT(*) FROM api_requests 
        WHERE user_id = %s AND request_date = %s
    """, (user_id, today))
    count = cursor.fetchone()[0]
    
    conn.close()
    
    # بررسی محدودیت
    limit = 1000 if is_premium else 20
    return count < limit

def log_api_request(user_id, endpoint):
    """ثبت درخواست API کاربر - PostgreSQL Compatible"""
    conn = get_connection()
    cursor = conn.cursor()
    
    today = datetime.date.today()
    
    cursor.execute("""
        INSERT INTO api_requests (user_id, endpoint, request_date) 
        VALUES (%s, %s, %s)
    """, (user_id, endpoint, today))
    
    conn.commit()
    conn.close()

def get_user_api_stats(user_id):
    """دریافت آمار درخواست‌های API کاربر - PostgreSQL Compatible"""
    conn = get_connection()
    cursor = conn.cursor()
    
    today = datetime.date.today()
    
    # تعداد درخواست‌های امروز
    cursor.execute("""
        SELECT COUNT(*) FROM api_requests 
        WHERE user_id = %s AND request_date = %s
    """, (user_id, today))
    today_count = cursor.fetchone()[0]
    
    # تعداد کل درخواست‌ها
    cursor.execute("""
        SELECT COUNT(*) FROM api_requests 
        WHERE user_id = %s
    """, (user_id,))
    total_count = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "today": today_count,
        "total": total_count
    }

# متدهای جدید برای migration
def migrate_from_sqlite_to_postgresql():
    """انتقال داده‌ها از SQLite به PostgreSQL - یکبار مصرف"""
    print("🔄 Starting migration from SQLite to PostgreSQL...")
    
    # اتصال به SQLite
    sqlite_conn = sqlite3.connect('bot_database.db')
    sqlite_cursor = sqlite_conn.cursor()
    
    # اتصال به PostgreSQL
    pg_conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    pg_cursor = pg_conn.cursor()
    
    try:
        # Migration users table
        print("📥 Migrating users...")
        sqlite_cursor.execute("SELECT * FROM users")
        users = sqlite_cursor.fetchall()
        
        for user in users:
            pg_cursor.execute("""
                INSERT INTO users (user_id, username, subscription_end, subscription_type, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                username = EXCLUDED.username,
                subscription_end = EXCLUDED.subscription_end,
                subscription_type = EXCLUDED.subscription_type,
                is_active = EXCLUDED.is_active
            """, user)
        
        # Migration transactions table
        print("💳 Migrating transactions...")
        sqlite_cursor.execute("SELECT * FROM transactions")
        transactions = sqlite_cursor.fetchall()
        
        for transaction in transactions:
            # Skip id (auto-increment)
            pg_cursor.execute("""
                INSERT INTO transactions (user_id, txid, wallet_address, amount, subscription_type, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, transaction[1:])  # Skip first column (id)
        
        # Migration api_requests table
        print("📊 Migrating API requests...")
        try:
            sqlite_cursor.execute("SELECT * FROM api_requests")
            api_requests = sqlite_cursor.fetchall()
            
            for request in api_requests:
                pg_cursor.execute("""
                    INSERT INTO api_requests (user_id, endpoint, request_date, created_at)
                    VALUES (%s, %s, %s, %s)
                """, request[1:])  # Skip first column (id)
        except sqlite3.OperationalError:
            print("⚠️ api_requests table not found in SQLite, skipping...")
        
        pg_conn.commit()
        print("✅ Migration completed successfully!")
        
        # آمار migration
        pg_cursor.execute("SELECT COUNT(*) FROM users")
        users_count = pg_cursor.fetchone()[0]
        
        pg_cursor.execute("SELECT COUNT(*) FROM transactions")
        transactions_count = pg_cursor.fetchone()[0]
        
        print(f"📊 Migrated: {users_count} users, {transactions_count} transactions")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        pg_conn.rollback()
        raise
    finally:
        sqlite_conn.close()
        pg_conn.close()

def create_referral_relationship(referrer_code, referred_user_id):
    """ایجاد رابطه رفرال بین دو کاربر"""
    conn = get_connection()
    cursor = conn.cursor()
    is_postgres = hasattr(conn, 'server_version')
    
    try:
        # پیدا کردن referrer از روی کد
        if is_postgres:
            cursor.execute("SELECT user_id FROM users WHERE referral_code = %s", (referrer_code,))
        else:
            cursor.execute("SELECT user_id FROM users WHERE referral_code = ?", (referrer_code,))
        
        referrer = cursor.fetchone()
        
        if not referrer:
            conn.close()
            return {"success": False, "error": "کد رفرال نامعتبر"}
        
        referrer_id = referrer[0]
        
        # جلوگیری از خود-رفرال
        if referrer_id == referred_user_id:
            conn.close()
            return {"success": False, "error": "نمی‌توانید خودتان را دعوت کنید"}
        
        # بررسی وجود رابطه قبلی
        if is_postgres:
            cursor.execute(
                "SELECT id FROM referrals WHERE referrer_id = %s AND referred_id = %s",
                (referrer_id, referred_user_id)
            )
        else:
            cursor.execute(
                "SELECT id FROM referrals WHERE referrer_id = ? AND referred_id = ?",
                (referrer_id, referred_user_id)
            )
        
        existing = cursor.fetchone()
        
        if existing:
            conn.close()
            return {"success": False, "error": "رابطه رفرال قبلاً ثبت شده"}
        
        # ایجاد رابطه جدید
        if is_postgres:
            cursor.execute("""
                INSERT INTO referrals (referrer_id, referred_id, status) 
                VALUES (%s, %s, 'pending')
            """, (referrer_id, referred_user_id))
        else:
            cursor.execute("""
                INSERT INTO referrals (referrer_id, referred_id, status) 
                VALUES (?, ?, 'pending')
            """, (referrer_id, referred_user_id))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True, 
            "referrer_id": referrer_id,
            "message": f"رابطه رفرال بین {referrer_id} و {referred_user_id} ثبت شد"
        }
        
    except Exception as e:
        conn.close()
        return {"success": False, "error": f"خطا در ثبت رفرال: {str(e)}"}

def calculate_commission(referrer_id, referred_user_id, plan_type, transaction_id):
    """محاسبه و ثبت کمیسیون برای رفرال موفق"""
    conn = get_connection()
    cursor = conn.cursor()
    is_postgres = hasattr(conn, 'server_version')
    
    try:
        # دریافت تنظیمات کمیسیون کاربر
        if is_postgres:
            cursor.execute("SELECT custom_commission_rate FROM users WHERE user_id = %s", (referrer_id,))
        else:
            cursor.execute("SELECT custom_commission_rate FROM users WHERE user_id = ?", (referrer_id,))
        
        user_data = cursor.fetchone()
        custom_rate = user_data[0] if user_data and user_data[0] else None
        
        # محاسبه کمیسیون پایه
        if plan_type == "ماهانه":
            base_commission = 7.00
        elif plan_type == "سه_ماهه":
            base_commission = 16.00
        else:
            base_commission = 0.00
        
        # اعمال نرخ سفارشی اگر وجود دارد
        if custom_rate:
            if plan_type == "ماهانه":
                base_commission = 25.00 * (custom_rate / 100)
            elif plan_type == "سه_ماهه":
                base_commission = 65.00 * (custom_rate / 100)
        
        # محاسبه بونوس حجمی
        if is_postgres:
            cursor.execute("SELECT COUNT(*) FROM commissions WHERE referrer_id = %s AND status = 'pending'", (referrer_id,))
        else:
            cursor.execute("SELECT COUNT(*) FROM commissions WHERE referrer_id = ? AND status = 'pending'", (referrer_id,))
        
        successful_referrals = cursor.fetchone()[0] + 1
        
        bonus_amount = 0.00
        if successful_referrals >= 10:
            bonus_amount = 5.00
        elif successful_referrals >= 5:
            bonus_amount = 2.00
        
        total_amount = base_commission + bonus_amount
        
        # ثبت کمیسیون
        if is_postgres:
            cursor.execute("""
                INSERT INTO commissions 
                (referrer_id, referred_id, transaction_id, plan_type, 
                 commission_amount, bonus_amount, total_amount, status) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending')
            """, (referrer_id, referred_user_id, transaction_id, plan_type,
                  base_commission, bonus_amount, total_amount))
        else:
            cursor.execute("""
                INSERT INTO commissions 
                (referrer_id, referred_id, transaction_id, plan_type, 
                 commission_amount, bonus_amount, total_amount, status) 
                VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
            """, (referrer_id, referred_user_id, transaction_id, plan_type,
                  base_commission, bonus_amount, total_amount))
        
        # به‌روزرسانی وضعیت رفرال
        if is_postgres:
            cursor.execute("UPDATE referrals SET status = 'completed' WHERE referrer_id = %s AND referred_id = %s", (referrer_id, referred_user_id))
            cursor.execute("UPDATE users SET total_earned = total_earned + %s WHERE user_id = %s", (total_amount, referrer_id))
        else:
            cursor.execute("UPDATE referrals SET status = 'completed' WHERE referrer_id = ? AND referred_id = ?", (referrer_id, referred_user_id))
            cursor.execute("UPDATE users SET total_earned = total_earned + ? WHERE user_id = ?", (total_amount, referrer_id))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "commission_amount": base_commission,
            "bonus_amount": bonus_amount,
            "total_amount": total_amount,
            "successful_referrals": successful_referrals
        }
        
    except Exception as e:
        conn.close()
        return {"success": False, "error": f"خطا در محاسبه کمیسیون: {str(e)}"}

def get_referral_stats(user_id):
    """دریافت آمار کامل رفرال کاربر"""
    conn = get_connection()
    cursor = conn.cursor()
    is_postgres = hasattr(conn, 'server_version')
    
    try:
        # اطلاعات پایه کاربر
        if is_postgres:
            cursor.execute("""
                SELECT referral_code, total_earned, total_paid, custom_commission_rate
                FROM users WHERE user_id = %s
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT referral_code, total_earned, total_paid, custom_commission_rate
                FROM users WHERE user_id = ?
            """, (user_id,))
        
        user_data = cursor.fetchone()
        if not user_data:
            conn.close()
            return {"success": False, "error": "کاربر یافت نشد"}
        
        referral_code, total_earned, total_paid, custom_rate = user_data
        
        # لیست خریداران موفق
        if is_postgres:
            cursor.execute("""
                SELECT u.username, u.user_id, c.plan_type, c.total_amount, c.created_at, c.status
                FROM commissions c
                JOIN users u ON c.referred_id = u.user_id
                WHERE c.referrer_id = %s
                ORDER BY c.created_at DESC
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT u.username, u.user_id, c.plan_type, c.total_amount, c.created_at, c.status
                FROM commissions c
                JOIN users u ON c.referred_id = u.user_id
                WHERE c.referrer_id = ?
                ORDER BY c.created_at DESC
            """, (user_id,))
        
        successful_buyers = cursor.fetchall()
        
        # آمار کمیسیون‌ها
        if is_postgres:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_referrals,
                    SUM(CASE WHEN status = 'pending' THEN total_amount ELSE 0 END) as pending_amount,
                    SUM(CASE WHEN status = 'paid' THEN total_amount ELSE 0 END) as paid_amount
                FROM commissions WHERE referrer_id = %s
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_referrals,
                    SUM(CASE WHEN status = 'pending' THEN total_amount ELSE 0 END) as pending_amount,
                    SUM(CASE WHEN status = 'paid' THEN total_amount ELSE 0 END) as paid_amount
                FROM commissions WHERE referrer_id = ?
            """, (user_id,))
        
        commission_stats = cursor.fetchone()
        
        conn.close()
        
        return {
            "success": True,
            "referral_code": referral_code,
            "total_earned": float(total_earned or 0),
            "total_paid": float(total_paid or 0),
            "pending_amount": float(commission_stats[1] or 0),
            "successful_referrals": commission_stats[0] or 0,
            "custom_commission_rate": custom_rate,
            "buyers": [
                {
                    "username": buyer[0] or f"User_{buyer[1]}",
                    "user_id": buyer[1],
                    "plan_type": buyer[2],
                    "amount": float(buyer[3]),
                    "date": str(buyer[4]),
                    "status": buyer[5]
                }
                for buyer in successful_buyers
            ]
        }
        
    except Exception as e:
        conn.close()
        return {"success": False, "error": f"خطا در دریافت آمار: {str(e)}"}

def get_admin_referral_stats():
    """آمار کامل رفرال برای ادمین"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # لیست همه referrer ها با آمار
        cursor.execute("""
            SELECT 
                u.user_id,
                u.username,
                u.referral_code,
                u.custom_commission_rate,
                u.total_earned,
                u.total_paid,
                COUNT(c.id) as total_referrals,
                SUM(CASE WHEN c.status = 'pending' THEN c.total_amount ELSE 0 END) as pending_amount
            FROM users u
            LEFT JOIN commissions c ON u.user_id = c.referrer_id
            WHERE u.total_earned > 0 OR c.id IS NOT NULL
            GROUP BY u.user_id, u.username, u.referral_code, u.custom_commission_rate, u.total_earned, u.total_paid
            ORDER BY u.total_earned DESC
        """)
        
        referrers = cursor.fetchall()
        
        # آمار کلی سیستم
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT referrer_id) as total_referrers,
                COUNT(*) as total_commissions,
                SUM(total_amount) as total_commissions_amount,
                SUM(CASE WHEN status = 'pending' THEN total_amount ELSE 0 END) as pending_payments,
                SUM(CASE WHEN status = 'paid' THEN total_amount ELSE 0 END) as paid_amount
            FROM commissions
        """)
        
        system_stats = cursor.fetchone()
        
        conn.close()
        
        return {
            "success": True,
            "system_stats": {
                "total_referrers": system_stats[0] or 0,
                "total_commissions": system_stats[1] or 0,
                "total_commissions_amount": float(system_stats[2] or 0),
                "pending_payments": float(system_stats[3] or 0),
                "paid_amount": float(system_stats[4] or 0)
            },
            "referrers": [
                {
                    "user_id": ref[0],
                    "username": ref[1] or f"User_{ref[0]}",
                    "referral_code": ref[2],
                    "custom_rate": ref[3],
                    "total_earned": float(ref[4] or 0),
                    "total_paid": float(ref[5] or 0),
                    "total_referrals": ref[6] or 0,
                    "pending_amount": float(ref[7] or 0)
                }
                for ref in referrers
            ]
        }
        
    except Exception as e:
        conn.close()
        return {"success": False, "error": f"خطا در دریافت آمار ادمین: {str(e)}"}

def mark_commission_as_paid(referrer_id, amount):
    """تصویه حساب کمیسیون کاربر"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # علامت‌گذاری کمیسیون‌های pending به عنوان paid
        cursor.execute("""
            UPDATE commissions 
            SET status = 'paid', paid_at = CURRENT_TIMESTAMP 
            WHERE referrer_id = %s AND status = 'pending'
        """, (referrer_id,))
        
        # به‌روزرسانی total_paid کاربر
        cursor.execute("""
            UPDATE users 
            SET total_paid = total_paid + %s 
            WHERE user_id = %s
        """, (amount, referrer_id))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": f"کمیسیون {amount}$ برای کاربر {referrer_id} تصویه شد"}
        
    except Exception as e:
        conn.close()
        return {"success": False, "error": f"خطا در تصویه حساب: {str(e)}"}

def get_referral_settings():
    """دریافت تنظیمات سیستم رفرال"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT setting_key, setting_value FROM referral_settings")
    settings = cursor.fetchall()
    
    conn.close()
    
    return {setting[0]: setting[1] for setting in settings}

def update_referral_setting(key, value):
    """به‌روزرسانی تنظیمات سیستم رفرال"""
    conn = get_connection()
    cursor = conn.cursor()
    
    is_postgres = hasattr(conn, 'server_version')
    
    if is_postgres:
        cursor.execute("""
            INSERT INTO referral_settings (setting_key, setting_value) 
            VALUES (%s, %s)
            ON CONFLICT (setting_key) DO UPDATE SET 
            setting_value = EXCLUDED.setting_value,
            updated_at = CURRENT_TIMESTAMP
        """, (key, value))
    else:
        cursor.execute("""
            INSERT OR REPLACE INTO referral_settings (setting_key, setting_value) 
            VALUES (?, ?)
        """, (key, value))
    
    conn.commit()
    conn.close()
    
    return {"success": True, "message": f"تنظیم {key} به {value} تغییر یافت"}

# === TNT PLANS & LIMIT MANAGEMENT ===

def get_tnt_plan_info(plan_name: str):
    """دریافت اطلاعات پلن TNT"""
    conn = get_connection()
    cursor = conn.cursor()
    is_postgres = hasattr(conn, 'server_version')
    
    try:
        if is_postgres:
            cursor.execute("""
                SELECT plan_name, plan_display_name, price_usd, monthly_limit, 
                       hourly_limit, vip_access, is_active
                FROM tnt_plans 
                WHERE plan_name = %s AND is_active = true
            """, (plan_name,))
        else:
            cursor.execute("""
                SELECT plan_name, plan_display_name, price_usd, monthly_limit, 
                       hourly_limit, vip_access, is_active
                FROM tnt_plans 
                WHERE plan_name = ? AND is_active = 1
            """, (plan_name,))
        
        plan_data = cursor.fetchone()
        conn.close()
        
        if plan_data:
            return {
                "plan_name": plan_data[0],
                "display_name": plan_data[1],
                "price_usd": float(plan_data[2]),
                "monthly_limit": plan_data[3],
                "hourly_limit": plan_data[4],
                "vip_access": bool(plan_data[5]),
                "is_active": bool(plan_data[6])
            }
        
        return None
        
    except Exception as e:
        conn.close()
        print(f"Error getting TNT plan info: {e}")
        return None

def get_user_tnt_plan(user_id: int):
    """دریافت پلن TNT کاربر"""
    conn = get_connection()
    cursor = conn.cursor()
    is_postgres = hasattr(conn, 'server_version')
    
    try:
        if is_postgres:
            cursor.execute("""
                SELECT tnt_plan_type, tnt_plan_start, tnt_plan_end, 
                       tnt_monthly_limit, tnt_hourly_limit
                FROM users 
                WHERE user_id = %s
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT tnt_plan_type, tnt_plan_start, tnt_plan_end, 
                       tnt_monthly_limit, tnt_hourly_limit
                FROM users 
                WHERE user_id = ?
            """, (user_id,))
        
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            plan_type, plan_start, plan_end, monthly_limit, hourly_limit = user_data
            
            # بررسی انقضای پلن - اصلاح شده
            plan_active = False
            expired = False
            
            if plan_end and plan_type != "FREE":
                try:
                    from datetime import datetime
                    # پردازش مناسب datetime string
                    if isinstance(plan_end, str):
                        # برای SQLite که datetime را string ذخیره می‌کند
                        end_date = datetime.fromisoformat(plan_end.replace('Z', '').replace('+00:00', ''))
                    else:
                        # برای PostgreSQL که datetime object دارد
                        end_date = plan_end
                    
                    now = datetime.now()
                    
                    if now > end_date:
                        # پلن منقضی شده - به FREE تبدیل کن
                        expired = True
                        reset_user_to_free_plan(user_id)
                        return {
                            "plan_type": "FREE",
                            "monthly_limit": 0,
                            "hourly_limit": 0,
                            "plan_active": False,
                            "expired": True
                        }
                    else:
                        plan_active = True
                        
                except Exception as e:
                    print(f"Error parsing plan_end date: {e}")
                    # در صورت خطا، پلن را فعال در نظر بگیر
                    plan_active = True
            
            return {
                "plan_type": plan_type or "FREE",
                "monthly_limit": monthly_limit or 0,
                "hourly_limit": hourly_limit or 0,
                "plan_start": plan_start,
                "plan_end": plan_end,
                "plan_active": plan_active,
                "expired": expired
            }
        
        # کاربر جدید - پلن FREE
        return {
            "plan_type": "FREE",
            "monthly_limit": 0,
            "hourly_limit": 0,
            "plan_active": False,
            "expired": False
        }
        
    except Exception as e:
        conn.close()
        print(f"Error getting user TNT plan: {e}")
        return None

def check_tnt_analysis_limit(user_id: int):
    """بررسی محدودیت تحلیل TNT کاربر"""
    from datetime import datetime, date
    
    # دریافت پلن کاربر
    user_plan = get_user_tnt_plan(user_id)
    if not user_plan:
        return {"allowed": False, "reason": "خطا در دریافت اطلاعات کاربر"}
    
    # اگر پلن FREE است
    if user_plan["plan_type"] == "FREE":
        return {"allowed": False, "reason": "plan_required", "message": "برای استفاده از تحلیل TNT نیاز به اشتراک دارید"}
    
    # اگر پلن منقضی شده
    if user_plan["expired"] or not user_plan["plan_active"]:
        return {"allowed": False, "reason": "plan_expired", "message": "اشتراک شما منقضی شده است"}
    
    # بررسی محدودیت ماهانه
    monthly_usage = get_user_monthly_usage(user_id)
    if monthly_usage >= user_plan["monthly_limit"]:
        return {
            "allowed": False, 
            "reason": "monthly_limit", 
            "message": f"سقف ماهانه شما ({user_plan['monthly_limit']} تحلیل) تمام شده است",
            "usage": monthly_usage,
            "limit": user_plan["monthly_limit"]
        }
    
    # بررسی محدودیت ساعتی
    hourly_usage = get_user_hourly_usage(user_id)
    if hourly_usage >= user_plan["hourly_limit"]:
        return {
            "allowed": False,
            "reason": "hourly_limit", 
            "message": f"سقف ساعتی شما ({user_plan['hourly_limit']} تحلیل) تمام شده است",
            "usage": hourly_usage,
            "limit": user_plan["hourly_limit"]
        }
    
    # همه چیز OK
    return {
        "allowed": True,
        "monthly_usage": monthly_usage,
        "monthly_limit": user_plan["monthly_limit"],
        "hourly_usage": hourly_usage,
        "hourly_limit": user_plan["hourly_limit"],
        "remaining_monthly": user_plan["monthly_limit"] - monthly_usage,
        "remaining_hourly": user_plan["hourly_limit"] - hourly_usage
    }

def get_user_monthly_usage(user_id: int):
    """دریافت تعداد استفاده ماهانه کاربر"""
    from datetime import datetime, date
    
    conn = get_connection()
    cursor = conn.cursor()
    is_postgres = hasattr(conn, 'server_version')
    
    try:
        # محاسبه ابتدای ماه جاری
        now = datetime.now()
        start_of_month = date(now.year, now.month, 1)
        
        if is_postgres:
            cursor.execute("""
                SELECT COALESCE(SUM(analysis_count), 0) 
                FROM tnt_usage_tracking 
                WHERE user_id = %s AND usage_date >= %s
            """, (user_id, start_of_month))
        else:
            cursor.execute("""
                SELECT COALESCE(SUM(analysis_count), 0) 
                FROM tnt_usage_tracking 
                WHERE user_id = ? AND usage_date >= ?
            """, (user_id, start_of_month.isoformat()))
        
        monthly_usage = cursor.fetchone()[0]
        conn.close()
        
        return int(monthly_usage)
        
    except Exception as e:
        conn.close()
        print(f"Error getting monthly usage: {e}")
        return 0

def get_user_hourly_usage(user_id: int):
    """دریافت تعداد استفاده ساعت جاری کاربر"""
    from datetime import datetime, date
    
    conn = get_connection()
    cursor = conn.cursor()
    is_postgres = hasattr(conn, 'server_version')
    
    try:
        # ساعت و تاریخ جاری
        now = datetime.now()
        current_date = now.date()
        current_hour = now.hour
        
        if is_postgres:
            cursor.execute("""
                SELECT COALESCE(analysis_count, 0) 
                FROM tnt_usage_tracking 
                WHERE user_id = %s AND usage_date = %s AND usage_hour = %s
            """, (user_id, current_date, current_hour))
        else:
            cursor.execute("""
                SELECT COALESCE(analysis_count, 0) 
                FROM tnt_usage_tracking 
                WHERE user_id = ? AND usage_date = ? AND usage_hour = ?
            """, (user_id, current_date.isoformat(), current_hour))
        
        result = cursor.fetchone()
        hourly_usage = result[0] if result else 0
        conn.close()
        
        return int(hourly_usage)
        
    except Exception as e:
        conn.close()
        print(f"Error getting hourly usage: {e}")
        return 0

def record_tnt_analysis_usage(user_id: int):
    """ثبت استفاده از تحلیل TNT"""
    from datetime import datetime, date
    
    conn = get_connection()
    cursor = conn.cursor()
    is_postgres = hasattr(conn, 'server_version')
    
    try:
        # ساعت و تاریخ جاری
        now = datetime.now()
        current_date = now.date()
        current_hour = now.hour
        
        if is_postgres:
            # PostgreSQL: INSERT ... ON CONFLICT
            cursor.execute("""
                INSERT INTO tnt_usage_tracking (user_id, usage_date, usage_hour, analysis_count)
                VALUES (%s, %s, %s, 1)
                ON CONFLICT (user_id, usage_date, usage_hour) 
                DO UPDATE SET 
                    analysis_count = tnt_usage_tracking.analysis_count + 1,
                    created_at = CURRENT_TIMESTAMP
            """, (user_id, current_date, current_hour))
        else:
            # SQLite: INSERT OR REPLACE
            # ابتدا چک کن آیا رکورد وجود دارد
            cursor.execute("""
                SELECT analysis_count FROM tnt_usage_tracking 
                WHERE user_id = ? AND usage_date = ? AND usage_hour = ?
            """, (user_id, current_date.isoformat(), current_hour))
            
            existing = cursor.fetchone()
            
            if existing:
                # اپدیت رکورد موجود
                cursor.execute("""
                    UPDATE tnt_usage_tracking 
                    SET analysis_count = analysis_count + 1, created_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND usage_date = ? AND usage_hour = ?
                """, (user_id, current_date.isoformat(), current_hour))
            else:
                # رکورد جدید
                cursor.execute("""
                    INSERT INTO tnt_usage_tracking (user_id, usage_date, usage_hour, analysis_count)
                    VALUES (?, ?, ?, 1)
                """, (user_id, current_date.isoformat(), current_hour))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Recorded TNT analysis usage for user {user_id} at {current_date} {current_hour}:00")
        return True
        
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"Error recording TNT usage: {e}")
        return False

def activate_tnt_subscription(user_id: int, plan_name: str, duration_months: int = 1):
    """فعال‌سازی اشتراک TNT کاربر"""
    from datetime import datetime, timedelta
    
    # دریافت اطلاعات پلن
    plan_info = get_tnt_plan_info(plan_name)
    if not plan_info:
        return {"success": False, "error": f"پلن {plan_name} یافت نشد"}
    
    conn = get_connection()
    cursor = conn.cursor()
    is_postgres = hasattr(conn, 'server_version')
    
    try:
        # محاسبه تاریخ شروع و پایان
        start_date = datetime.now()
        end_date = start_date + timedelta(days=30 * duration_months)
        
        if is_postgres:
            cursor.execute("""
                UPDATE users 
                SET tnt_plan_type = %s,
                    tnt_monthly_limit = %s,
                    tnt_hourly_limit = %s,
                    tnt_plan_start = %s,
                    tnt_plan_end = %s,
                    is_active = true
                WHERE user_id = %s
            """, (plan_name, plan_info["monthly_limit"], plan_info["hourly_limit"], 
                  start_date, end_date, user_id))
        else:
            cursor.execute("""
                UPDATE users 
                SET tnt_plan_type = ?,
                    tnt_monthly_limit = ?,
                    tnt_hourly_limit = ?,
                    tnt_plan_start = ?,
                    tnt_plan_end = ?,
                    is_active = 1
                WHERE user_id = ?
            """, (plan_name, plan_info["monthly_limit"], plan_info["hourly_limit"], 
                  start_date.isoformat(), end_date.isoformat(), user_id))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "plan_name": plan_name,
            "plan_display": plan_info["display_name"],
            "monthly_limit": plan_info["monthly_limit"],
            "hourly_limit": plan_info["hourly_limit"],
            "start_date": start_date.strftime('%Y-%m-%d'),
            "end_date": end_date.strftime('%Y-%m-%d'),
            "vip_access": plan_info["vip_access"]
        }
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return {"success": False, "error": f"خطا در فعال‌سازی اشتراک: {str(e)}"}

def reset_user_to_free_plan(user_id: int):
    """بازگردانی کاربر به پلن رایگان"""
    conn = get_connection()
    cursor = conn.cursor()
    is_postgres = hasattr(conn, 'server_version')
    
    try:
        if is_postgres:
            cursor.execute("""
                UPDATE users 
                SET tnt_plan_type = 'FREE',
                    tnt_monthly_limit = 0,
                    tnt_hourly_limit = 0,
                    tnt_plan_start = NULL,
                    tnt_plan_end = NULL,
                    is_active = false
                WHERE user_id = %s
            """, (user_id,))
        else:
            cursor.execute("""
                UPDATE users 
                SET tnt_plan_type = 'FREE',
                    tnt_monthly_limit = 0,
                    tnt_hourly_limit = 0,
                    tnt_plan_start = NULL,
                    tnt_plan_end = NULL,
                    is_active = 0
                WHERE user_id = ?
            """, (user_id,))
        
        conn.commit()
        conn.close()
        
        print(f"✅ User {user_id} reset to FREE plan")
        return True
        
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"Error resetting user to free plan: {e}")
        return False

def get_all_tnt_plans():
    """دریافت لیست تمام پلن‌های TNT فعال"""
    conn = get_connection()
    cursor = conn.cursor()
    is_postgres = hasattr(conn, 'server_version')
    
    try:
        if is_postgres:
            cursor.execute("""
                SELECT plan_name, plan_display_name, price_usd, monthly_limit, 
                       hourly_limit, vip_access
                FROM tnt_plans 
                WHERE is_active = true
                ORDER BY price_usd ASC
            """)
        else:
            cursor.execute("""
                SELECT plan_name, plan_display_name, price_usd, monthly_limit, 
                       hourly_limit, vip_access
                FROM tnt_plans 
                WHERE is_active = 1
                ORDER BY price_usd ASC
            """)
        
        plans = cursor.fetchall()
        conn.close()
        
        return [
            {
                "plan_name": plan[0],
                "display_name": plan[1],
                "price_usd": float(plan[2]),
                "monthly_limit": plan[3],
                "hourly_limit": plan[4],
                "vip_access": bool(plan[5])
            }
            for plan in plans
        ]
        
    except Exception as e:
        conn.close()
        print(f"Error getting TNT plans: {e}")
        return []

def get_user_tnt_usage_stats(user_id: int):
    """دریافت آمار کامل استفاده TNT کاربر"""
    user_plan = get_user_tnt_plan(user_id)
    if not user_plan:
        return None
    
    monthly_usage = get_user_monthly_usage(user_id)
    hourly_usage = get_user_hourly_usage(user_id)
    
    return {
        "plan_info": user_plan,
        "monthly_usage": monthly_usage,
        "hourly_usage": hourly_usage,
        "monthly_remaining": max(0, user_plan["monthly_limit"] - monthly_usage),
        "hourly_remaining": max(0, user_plan["hourly_limit"] - hourly_usage),
        "monthly_percentage": (monthly_usage / user_plan["monthly_limit"] * 100) if user_plan["monthly_limit"] > 0 else 0,
        "hourly_percentage": (hourly_usage / user_plan["hourly_limit"] * 100) if user_plan["hourly_limit"] > 0 else 0
    }
