#!/usr/bin/env python3
"""
Database Migration Script
آپدیت دیتابیس PostgreSQL برای سازگاری با SQLAlchemy Models
"""

import os
import sys
import logging
from datetime import datetime
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# تنظیم logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_url():
    """دریافت URL دیتابیس از متغیرهای محیطی"""
    return os.getenv('DATABASE_URL')

def connect_to_database():
    """اتصال به دیتابیس"""
    database_url = get_database_url()
    if not database_url:
        logger.error("DATABASE_URL environment variable not found")
        return None
    
    try:
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        logger.info("✅ Connected to PostgreSQL database")
        return conn
    except Exception as e:
        logger.error(f"❌ Failed to connect to database: {e}")
        return None

def check_column_exists(cursor, table_name, column_name):
    """بررسی وجود یک column در جدول"""
    try:
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s AND column_name = %s
        """, (table_name, column_name))
        return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"Error checking column {column_name}: {e}")
        return False

def check_table_exists(cursor, table_name):
    """بررسی وجود جدول"""
    try:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = %s
        """, (table_name,))
        return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"Error checking table {table_name}: {e}")
        return False

def migrate_users_table(cursor):
    """Migration جدول users"""
    logger.info("🔄 Migrating users table...")
    
    # بررسی وجود جدول
    if not check_table_exists(cursor, 'users'):
        logger.info("📝 Creating users table...")
        cursor.execute("""
            CREATE TABLE users (
                user_id BIGINT PRIMARY KEY,
                username VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                subscription_end TIMESTAMP,
                subscription_type VARCHAR(20) DEFAULT 'free',
                is_active BOOLEAN DEFAULT true,
                tnt_plan_type VARCHAR(20) DEFAULT 'free',
                tnt_monthly_limit INTEGER DEFAULT 0,
                tnt_hourly_limit INTEGER DEFAULT 0,
                tnt_plan_start TIMESTAMP,
                tnt_plan_end TIMESTAMP,
                referral_code VARCHAR(50) UNIQUE,
                custom_commission_rate DECIMAL(5,2),
                total_earned DECIMAL(10,2) DEFAULT 0.00,
                total_paid DECIMAL(10,2) DEFAULT 0.00
            )
        """)
        logger.info("✅ Users table created")
        return
    
    # اضافه کردن column های جدید
    new_columns = [
        ('tnt_plan_type', "VARCHAR(20) DEFAULT 'free'"),
        ('tnt_monthly_limit', "INTEGER DEFAULT 0"),
        ('tnt_hourly_limit', "INTEGER DEFAULT 0"),
        ('tnt_plan_start', "TIMESTAMP"),
        ('tnt_plan_end', "TIMESTAMP"),
        ('referral_code', "VARCHAR(50) UNIQUE"),
        ('custom_commission_rate', "DECIMAL(5,2)"),
        ('total_earned', "DECIMAL(10,2) DEFAULT 0.00"),
        ('total_paid', "DECIMAL(10,2) DEFAULT 0.00")
    ]
    
    for column_name, column_type in new_columns:
        if not check_column_exists(cursor, 'users', column_name):
            logger.info(f"➕ Adding column: {column_name}")
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
                logger.info(f"✅ Added column: {column_name}")
            except Exception as e:
                logger.error(f"❌ Failed to add column {column_name}: {e}")

def migrate_referrals_table(cursor):
    """Migration جدول referrals"""
    logger.info("🔄 Migrating referrals table...")
    
    if not check_table_exists(cursor, 'referrals'):
        logger.info("📝 Creating referrals table...")
        cursor.execute("""
            CREATE TABLE referrals (
                id SERIAL PRIMARY KEY,
                referrer_id BIGINT NOT NULL,
                referred_id BIGINT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                commission_earned DECIMAL(10,2) DEFAULT 0.00,
                FOREIGN KEY (referrer_id) REFERENCES users(user_id),
                FOREIGN KEY (referred_id) REFERENCES users(user_id),
                UNIQUE(referred_id)
            )
        """)
        logger.info("✅ Referrals table created")

def migrate_api_logs_table(cursor):
    """Migration جدول api_logs"""
    logger.info("🔄 Migrating api_logs table...")
    
    if not check_table_exists(cursor, 'api_logs'):
        logger.info("📝 Creating api_logs table...")
        cursor.execute("""
            CREATE TABLE api_logs (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                endpoint VARCHAR(100) NOT NULL,
                request_count INTEGER DEFAULT 1,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                response_data TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        logger.info("✅ API logs table created")

def migrate_subscriptions_table(cursor):
    """Migration جدول subscriptions"""
    logger.info("🔄 Migrating subscriptions table...")
    
    if not check_table_exists(cursor, 'subscriptions'):
        logger.info("📝 Creating subscriptions table...")
        cursor.execute("""
            CREATE TABLE subscriptions (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                plan_type VARCHAR(20) NOT NULL,
                start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_date TIMESTAMP NOT NULL,
                is_active BOOLEAN DEFAULT true,
                payment_amount DECIMAL(10,2),
                payment_method VARCHAR(50),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        logger.info("✅ Subscriptions table created")

def migrate_tnt_usage_table(cursor):
    """Migration جدول tnt_usage"""
    logger.info("🔄 Migrating tnt_usage table...")
    
    if not check_table_exists(cursor, 'tnt_usage'):
        logger.info("📝 Creating tnt_usage table...")
        cursor.execute("""
            CREATE TABLE tnt_usage (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                usage_date DATE DEFAULT CURRENT_DATE,
                hourly_count INTEGER DEFAULT 0,
                monthly_count INTEGER DEFAULT 0,
                last_request TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                UNIQUE(user_id, usage_date)
            )
        """)
        logger.info("✅ TNT usage table created")

def create_indexes(cursor):
    """ایجاد index های مفید"""
    logger.info("🔄 Creating database indexes...")
    
    indexes = [
        ("idx_users_referral_code", "users", "referral_code"),
        ("idx_referrals_referrer", "referrals", "referrer_id"),
        ("idx_referrals_referred", "referrals", "referred_id"),
        ("idx_api_logs_user", "api_logs", "user_id"),
        ("idx_api_logs_timestamp", "api_logs", "timestamp"),
        ("idx_subscriptions_user", "subscriptions", "user_id"),
        ("idx_tnt_usage_user", "tnt_usage", "user_id"),
        ("idx_tnt_usage_date", "tnt_usage", "usage_date")
    ]
    
    for index_name, table_name, column_name in indexes:
        try:
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS {index_name} 
                ON {table_name} ({column_name})
            """)
            logger.info(f"✅ Created index: {index_name}")
        except Exception as e:
            logger.error(f"❌ Failed to create index {index_name}: {e}")

def main():
    """تابع اصلی migration"""
    logger.info("🚀 Starting database migration...")
    
    # اتصال به دیتابیس
    conn = connect_to_database()
    if not conn:
        sys.exit(1)
    
    cursor = conn.cursor()
    
    try:
        # اجرای migration ها
        migrate_users_table(cursor)
        migrate_referrals_table(cursor)
        migrate_api_logs_table(cursor)
        migrate_subscriptions_table(cursor)
        migrate_tnt_usage_table(cursor)
        create_indexes(cursor)
        
        logger.info("🎉 Database migration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(1)
    
    finally:
        cursor.close()
        conn.close()
        logger.info("🔌 Database connection closed")

if __name__ == "__main__":
    main()
