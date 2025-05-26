import sqlite3
import datetime

def init_db():
    """ایجاد پایگاه داده و جداول مورد نیاز"""
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    
    # ایجاد جدول کاربران
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
    
    # ایجاد جدول تراکنش‌ها
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
    
    # ایجاد جدول برای ذخیره درخواست‌های API (برای محدودیت روزانه)
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

def check_subscription(user_id):
    """بررسی وضعیت اشتراک کاربر"""
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT subscription_end, is_active FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return False
    
    end_date_str, is_active = result
    if not is_active or not end_date_str:
        conn.close()
        return False
    
    end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
    today = datetime.date.today()
    
    conn.close()
    return end_date >= today

def register_user(user_id, username):
    """ثبت کاربر جدید در دیتابیس"""
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (user_id, username) VALUES (?, ?)",
            (user_id, username)
        )
        conn.commit()
    
    conn.close()

def activate_subscription(user_id, duration_months, sub_type):
    """فعال‌سازی اشتراک کاربر"""
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    
    today = datetime.date.today()
    end_date = today + datetime.timedelta(days=30 * duration_months)
    
    cursor.execute(
        "UPDATE users SET subscription_end = ?, subscription_type = ?, is_active = 1 WHERE user_id = ?",
        (end_date.strftime('%Y-%m-%d'), sub_type, user_id)
    )
    
    conn.commit()
    conn.close()
    return end_date.strftime('%Y-%m-%d')

def get_user_info(user_id):
    """دریافت اطلاعات کاربر"""
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()
    
    if not user_data:
        conn.close()
        return None
    
    # دریافت تراکنش‌های اخیر کاربر
    cursor.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT 5", (user_id,))
    transactions = cursor.fetchall()
    
    conn.close()
    return {"user_data": user_data, "transactions": transactions}

def save_transaction(user_id, txid, wallet_address, amount, subscription_type):
    """ذخیره تراکنش جدید"""
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO transactions (user_id, txid, wallet_address, amount, subscription_type) VALUES (?, ?, ?, ?, ?)",
        (user_id, txid, wallet_address, amount, subscription_type)
    )
    
    conn.commit()
    conn.close()

def check_user_api_limit(user_id, is_premium=False):
    """بررسی محدودیت درخواست API کاربر"""
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    
    today = datetime.date.today()
    
    # شمارش درخواست‌های امروز
    cursor.execute(
        "SELECT COUNT(*) FROM api_requests WHERE user_id = ? AND request_date = ?",
        (user_id, today)
    )
    count = cursor.fetchone()[0]
    
    conn.close()
    
    # بررسی محدودیت
    limit = 1000 if is_premium else 20
    return count < limit

def log_api_request(user_id, endpoint):
    """ثبت درخواست API کاربر"""
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    
    today = datetime.date.today()
    
    cursor.execute(
        "INSERT INTO api_requests (user_id, endpoint, request_date) VALUES (?, ?, ?)",
        (user_id, endpoint, today)
    )
    
    conn.commit()
    conn.close()

def get_user_api_stats(user_id):
    """دریافت آمار درخواست‌های API کاربر"""
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    
    today = datetime.date.today()
    
    # تعداد درخواست‌های امروز
    cursor.execute(
        "SELECT COUNT(*) FROM api_requests WHERE user_id = ? AND request_date = ?",
        (user_id, today)
    )
    today_count = cursor.fetchone()[0]
    
    # تعداد کل درخواست‌ها
    cursor.execute(
        "SELECT COUNT(*) FROM api_requests WHERE user_id = ?",
        (user_id,)
    )
    total_count = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "today": today_count,
        "total": total_count
    }
