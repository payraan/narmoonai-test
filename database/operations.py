import sqlite3
import psycopg2
import psycopg2.extras
import datetime
import os

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
    """ایجاد پایگاه داده و جداول مورد نیاز - PostgreSQL Compatible"""
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
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
        
        # ایجاد ایندکس‌ها برای بهتر شدن عملکرد
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_users_subscription 
            ON users(subscription_end, is_active)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_api_requests_date 
            ON api_requests(user_id, request_date)
        ''')
        
    else:
        # SQLite syntax (development)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                subscription_end DATE,
                subscription_type TEXT,
                is_active BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

def register_user(user_id, username):
    """ثبت کاربر جدید در دیتابیس - PostgreSQL Compatible"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # PostgreSQL: ON CONFLICT, SQLite: INSERT OR IGNORE
    is_postgres = hasattr(conn, 'server_version')
    
    if is_postgres:
        cursor.execute("""
            INSERT INTO users (user_id, username) 
            VALUES (%s, %s) 
            ON CONFLICT (user_id) DO NOTHING
        """, (user_id, username))
    else:
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO users (user_id, username) VALUES (?, ?)",
                (user_id, username)
            )
    
    conn.commit()
    conn.close()

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

# تابع جدید برای migration
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
