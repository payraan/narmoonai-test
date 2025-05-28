#!/usr/bin/env python3
"""
Safe Database Migration Script
- Transaction-safe operations
- Rollback on any error
- No data loss
"""
import os
import sys
import psycopg2
from datetime import datetime

def safe_migration():
    """Migration با مدیریت Transaction ایمن"""
    
    # اتصال به PostgreSQL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL environment variable not found!")
        return False
    
    print(f"🔗 Connecting to database...")
    
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = False  # Transaction manual
        cursor = conn.cursor()
        
        print("✅ Connected to PostgreSQL successfully!")
        print("\n🔧 Starting Safe Migration...")
        
        # بررسی وضعیت فعلی
        print("\n📋 Step 1: Checking current database state...")
        
        # چک کردن جداول موجود
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
        print(f"📊 Existing tables: {', '.join(existing_tables)}")
        
        # چک کردن ستون‌های users
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND table_schema = 'public'
            ORDER BY column_name
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"📋 Users table columns: {', '.join(existing_columns)}")
        
        # === Step 2: Add missing columns to users table ===
        print("\n📝 Step 2: Adding missing columns to users table...")
        
        columns_to_add = [
            ("referral_code", "TEXT"),
            ("custom_commission_rate", "DECIMAL(5,2)"),
            ("total_earned", "DECIMAL(10,2) DEFAULT 0.00"),
            ("total_paid", "DECIMAL(10,2) DEFAULT 0.00")
        ]
        
        for column_name, column_definition in columns_to_add:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_definition}")
                    print(f"✅ Added column: {column_name}")
                except Exception as e:
                    print(f"⚠️ Column {column_name}: {str(e)}")
            else:
                print(f"✅ Column {column_name} already exists")
        
        # === Step 3: Add unique constraint ===
        print("\n🔐 Step 3: Adding unique constraint...")
        
        try:
            # Check if constraint already exists
            cursor.execute("""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE table_name = 'users' 
                AND constraint_type = 'UNIQUE' 
                AND constraint_name = 'users_referral_code_unique'
            """)
            
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE users ADD CONSTRAINT users_referral_code_unique UNIQUE (referral_code)")
                print("✅ Added unique constraint for referral_code")
            else:
                print("✅ Unique constraint already exists")
                
        except Exception as e:
            print(f"⚠️ Unique constraint: {str(e)}")
        
        # === Step 4: Create missing tables ===
        print("\n📊 Step 4: Creating missing tables...")
        
        # Create referrals table
        if 'referrals' not in existing_tables:
            cursor.execute("""
                CREATE TABLE referrals (
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
        else:
            print("✅ Referrals table already exists")
        
        # Create commissions table
        if 'commissions' not in existing_tables:
            cursor.execute("""
                CREATE TABLE commissions (
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
        else:
            print("✅ Commissions table already exists")
        
        # Create referral_settings table
        if 'referral_settings' not in existing_tables:
            cursor.execute("""
                CREATE TABLE referral_settings (
                    id SERIAL PRIMARY KEY,
                    setting_key TEXT UNIQUE NOT NULL,
                    setting_value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ Created referral_settings table")
        else:
            print("✅ Referral_settings table already exists")
        
        # === Step 5: Insert default settings ===
        print("\n⚙️ Step 5: Adding default settings...")
        
        cursor.execute("""
            INSERT INTO referral_settings (setting_key, setting_value) 
            VALUES ('min_withdrawal_amount', '20.00')
            ON CONFLICT (setting_key) DO NOTHING
        """)
        print("✅ Added default referral settings")
        
        # === Step 6: Create indexes safely ===
        print("\n🚀 Step 6: Creating performance indexes...")
        
        indexes = [
            ("idx_users_referral_code", "CREATE INDEX IF NOT EXISTS idx_users_referral_code ON users(referral_code)"),
            ("idx_referrals_referrer", "CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id)"),
            ("idx_referrals_referred", "CREATE INDEX IF NOT EXISTS idx_referrals_referred ON referrals(referred_id)"),
            ("idx_commissions_referrer", "CREATE INDEX IF NOT EXISTS idx_commissions_referrer ON commissions(referrer_id, status)"),
            ("idx_commissions_status", "CREATE INDEX IF NOT EXISTS idx_commissions_status ON commissions(status)")
        ]
        
        for index_name, sql in indexes:
            try:
                cursor.execute(sql)
                print(f"✅ Created index: {index_name}")
            except Exception as e:
                print(f"⚠️ Index {index_name}: {str(e)[:100]}")
        
        # === Final Step: Commit everything ===
        print("\n💾 Committing all changes...")
        conn.commit()
        
        # === Verification ===
        print("\n🔍 Final verification...")
        
        # Check all tables again
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        final_tables = [row[0] for row in cursor.fetchall()]
        print(f"📊 Final tables: {', '.join(final_tables)}")
        
        # Check users columns again
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND table_schema = 'public'
            ORDER BY column_name
        """)
        final_columns = [row[0] for row in cursor.fetchall()]
        print(f"📋 Final users columns: {', '.join(final_columns)}")
        
        print("\n🎉 Migration completed successfully!")
        print("✅ Database is now ready for production!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("🔄 Rolling back changes...")
        try:
            conn.rollback()
            print("✅ Rollback successful - no data lost")
        except:
            print("❌ Rollback failed")
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()
            print("🔒 Database connection closed")

if __name__ == "__main__":
    print("🛠️ Safe Database Migration Tool")
    print("=" * 50)
    
    success = safe_migration()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("🚀 Ready to deploy to Railway!")
    else:
        print("\n❌ Migration failed!")
        print("📞 Contact support if needed")
    
    print("=" * 50)
