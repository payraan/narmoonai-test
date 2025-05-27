#!/usr/bin/env python3
"""
اسکریپت تعمیر دیتابیس - اجرای ایمن Migration برای Railway
"""
import os
import sys
import psycopg2
from datetime import datetime

def fix_database_migration():
    """تعمیر مشکلات migration دیتابیس"""
    
    # اتصال به PostgreSQL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL environment variable not found!")
        return False
    
    print(f"🔗 Connecting to database...")
    
    try:
        conn = psycopg2.connect(database_url)
        print("✅ Connected to PostgreSQL successfully!")
        
        # تنظیم autocommit برای جلوگیری از transaction مشکلات
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("\n🔧 Starting Database Repair...")
        
        # 1. بررسی و اضافه کردن فیلدهای referral به users table
        print("\n📝 Step 1: Adding referral columns to users table...")
        
        referral_columns = [
            ("referral_code", "TEXT"),
            ("custom_commission_rate", "DECIMAL(5,2)"),
            ("total_earned", "DECIMAL(10,2) DEFAULT 0.00"),
            ("total_paid", "DECIMAL(10,2) DEFAULT 0.00")
        ]
        
        for column_name, column_type in referral_columns:
            try:
                # بررسی وجود column
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='users' AND column_name=%s
                """, (column_name,))
                
                if not cursor.fetchone():
                    # اضافه کردن column
                    sql = f"ALTER TABLE users ADD COLUMN {column_name} {column_type}"
                    cursor.execute(sql)
                    print(f"✅ Added column: {column_name}")
                else:
                    print(f"⚠️  Column already exists: {column_name}")
                    
            except Exception as e:
                print(f"❌ Error adding column {column_name}: {e}")
        
        # 2. اضافه کردن UNIQUE constraint برای referral_code
        print("\n🔐 Step 2: Adding unique constraint for referral_code...")
        try:
            cursor.execute("""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE table_name='users' AND constraint_type='UNIQUE' 
                AND constraint_name LIKE '%referral_code%'
            """)
            
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE users ADD CONSTRAINT users_referral_code_unique UNIQUE (referral_code)")
                print("✅ Added unique constraint for referral_code")
            else:
                print("⚠️  Unique constraint already exists for referral_code")
                
        except Exception as e:
            print(f"❌ Error adding unique constraint: {e}")
        
        # 3. ایجاد جداول جدید referral system
        print("\n📊 Step 3: Creating referral system tables...")
        
        # جدول referrals
        try:
            cursor.execute("""
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
            """)
            print("✅ Created referrals table")
        except Exception as e:
            print(f"❌ Error creating referrals table: {e}")
        
        # جدول commissions
        try:
            cursor.execute("""
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
            """)
            print("✅ Created commissions table")
        except Exception as e:
            print(f"❌ Error creating commissions table: {e}")
        
        # جدول referral_settings
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS referral_settings (
                    id SERIAL PRIMARY KEY,
                    setting_key TEXT UNIQUE NOT NULL,
                    setting_value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Created referral_settings table")
        except Exception as e:
            print(f"❌ Error creating referral_settings table: {e}")
        
        # 4. ایجاد indexes برای بهبود performance
        print("\n🚀 Step 4: Creating performance indexes...")
        
        indexes = [
            ("idx_users_referral_code", "CREATE INDEX IF NOT EXISTS idx_users_referral_code ON users(referral_code)"),
            ("idx_referrals_referrer", "CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id)"),
            ("idx_referrals_referred", "CREATE INDEX IF NOT EXISTS idx_referrals_referred ON referrals(referred_id)"),
            ("idx_commissions_referrer", "CREATE INDEX IF NOT EXISTS idx_commissions_referrer ON commissions(referrer_id, status)"),
            ("idx_commissions_status", "CREATE INDEX IF NOT EXISTS idx_commissions_status ON commissions(status)"),
        ]
        
        for index_name, sql in indexes:
            try:
                cursor.execute(sql)
                print(f"✅ Created index: {index_name}")
            except Exception as e:
                print(f"⚠️  Index {index_name}: {str(e)[:100]}")
        
        # 5. اضافه کردن تنظیمات پیش‌فرض
        print("\n⚙️  Step 5: Adding default settings...")
        try:
            cursor.execute("""
                INSERT INTO referral_settings (setting_key, setting_value) 
                VALUES ('min_withdrawal_amount', '20.00')
                ON CONFLICT (setting_key) DO NOTHING
            """)
            print("✅ Added default referral settings")
        except Exception as e:
            print(f"❌ Error adding settings: {e}")
        
        # 6. بررسی سلامت جداول
        print("\n🔍 Step 6: Health check...")
        
        tables_to_check = ['users', 'transactions', 'api_requests', 'referrals', 'commissions', 'referral_settings']
        
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"✅ Table {table}: {count} records")
            except Exception as e:
                print(f"❌ Table {table}: {e}")
        
        print("\n🎉 Database migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database migration failed: {e}")
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()
            print("🔒 Database connection closed")

if __name__ == "__main__":
    print("🛠️  Railway Database Migration Fixer")
    print("=" * 50)
    
    success = fix_database_migration()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("🚀 You can now restart your bot!")
    else:
        print("\n❌ Migration failed!")
        print("🔧 Check the logs above for errors")
    
    print("=" * 50)
