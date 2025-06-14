# database/migration.py - نسخه اصلاح شده برای سازگاری با SQLite و PostgreSQL

import sqlite3
from sqlalchemy import text
from .connection import db_manager

# برای مدیریت خطای "ستون تکراری" در PostgreSQL
try:
    import psycopg2
except ImportError:
    psycopg2 = None

def run_migration():
    """
    اجرای migration هوشمند برای اضافه کردن ستون‌های جدید.
    این تابع نوع دیتابیس را تشخیص داده و از دستورات SQL مناسب استفاده می‌کند.
    """
    print("🚀 Starting smart migration...")
    
    # لیستی از ستون‌هایی که می‌خواهیم اضافه شوند
    columns_to_add = {
        'tnt_plan_type': "VARCHAR(20) DEFAULT 'free'",
        'tnt_monthly_limit': "INTEGER DEFAULT 0",
        'tnt_hourly_limit': "INTEGER DEFAULT 0",
        'referral_code': "VARCHAR(50)",
        'custom_commission_rate': "DECIMAL(5,2)",
        'total_earned': "DECIMAL(10,2) DEFAULT 0.00",
        'total_paid': "DECIMAL(10,2) DEFAULT 0.00",
        'tnt_plan_start': "TIMESTAMP",
        'tnt_plan_end': "TIMESTAMP"
    }

    try:
        with db_manager.get_session() as session:
            # تشخیص نوع دیتابیس
            is_postgres = 'postgres' in db_manager.db_url

            for column, definition in columns_to_add.items():
                try:
                    if is_postgres:
                        # دستور مخصوص PostgreSQL که بهینه است
                        query = f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {column} {definition}"
                        session.execute(text(query))
                    else:
                        # دستور مخصوص SQLite (بدون IF NOT EXISTS)
                        query = f"ALTER TABLE users ADD COLUMN {column} {definition}"
                        session.execute(text(query))
                        
                except (sqlite3.OperationalError, getattr(psycopg2.errors, 'DuplicateColumn', Exception)) as e:
                    # اگر خطا به خاطر وجود داشتن ستون باشد، آن را نادیده می‌گیریم
                    if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                        print(f"✅ Column '{column}' already exists, skipping.")
                    else:
                        # اگر خطا به دلیل دیگری بود، آن را نمایش می‌دهیم
                        raise e

            session.commit()
            print("✅ Smart migration completed successfully!")
            return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        # در صورت بروز خطا، session.rollback() به طور خودکار توسط with db_manager.get_session() مدیریت می‌شود
        return False
