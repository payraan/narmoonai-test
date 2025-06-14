# database/migration.py - نسخه نهایی و ۱۰۰٪ اصلاح شده

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
    این تابع نوع دیتابیس را با روش استاندارد SQLAlchemy تشخیص می‌دهد.
    """
    print("🚀 Starting smart migration...")

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
            # --- این بخش با روش استاندارد اصلاح شد ---
            dialect_name = session.bind.dialect.name
            is_postgres = dialect_name == 'postgresql'
            # ----------------------------------------

            for column, definition in columns_to_add.items():
                try:
                    if is_postgres:
                        query = f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {column} {definition}"
                    else:
                        query = f"ALTER TABLE users ADD COLUMN {column} {definition}"

                    session.execute(text(query))

                except (sqlite3.OperationalError, getattr(psycopg2.errors, 'DuplicateColumn', Exception)) as e:
                    if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                        print(f"✅ Column '{column}' already exists, skipping.")
                    else:
                        raise e

            session.commit()
            print("✅ Smart migration completed successfully!")
            return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
