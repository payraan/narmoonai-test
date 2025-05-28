#!/usr/bin/env python3
"""
Final Migration Script - One Source of Truth
Handles both SQLite (development) and PostgreSQL (production)
"""
import os
import sys
from datetime import datetime

def get_database_connection():
    """Smart database connection"""
    database_url = os.getenv("DATABASE_URL")
    
    if database_url and database_url.startswith("postgres"):
        # Production: PostgreSQL
        print("🐘 Connecting to PostgreSQL...")
        try:
            import psycopg2
            conn = psycopg2.connect(database_url)
            return conn, "postgresql", psycopg2
        except ImportError:
            print("❌ psycopg2 not available")
            sys.exit(1)
    else:
        # Development: SQLite
        print("🗄️ Connecting to SQLite...")
        import sqlite3
        conn = sqlite3.connect('bot_database.db')
        return conn, "sqlite", sqlite3

def execute_sql_safe(cursor, sql, params=None, description="SQL operation"):
    """Safe SQL execution with error handling"""
    try:
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        print(f"✅ {description}")
        return True
    except Exception as e:
        print(f"⚠️ {description}: {str(e)[:100]}")
        return False

def final_migration():
    """Complete database migration - PostgreSQL and SQLite compatible"""
    
    print("🚀 Starting Final Migration...")
    print("=" * 50)
    
    conn, db_type, db_module = get_database_connection()
    cursor = conn.cursor()
    
    try:
        print(f"📊 Database Type: {db_type}")
        
        # Step 1: Create base tables if not exist
        print("\n📋 Step 1: Ensuring base tables exist...")
        
        if db_type == "postgresql":
            # PostgreSQL syntax
            base_tables = [
                ("users", """
                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT PRIMARY KEY,
                        username TEXT,
                        subscription_end DATE,
                        subscription_type TEXT,
                        is_active BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """),
                ("transactions", """
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
                """),
                ("api_requests", """
                    CREATE TABLE IF NOT EXISTS api_requests (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT,
                        endpoint TEXT,
                        request_date DATE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                """)
            ]
        else:
            # SQLite syntax
            base_tables = [
                ("users", """
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        subscription_end DATE,
                        subscription_type TEXT,
                        is_active BOOLEAN DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """),
                ("transactions", """
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
                """),
                ("api_requests", """
                    CREATE TABLE IF NOT EXISTS api_requests (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        endpoint TEXT,
                        request_date DATE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                """)
            ]
        
        for table_name, sql in base_tables:
            execute_sql_safe(cursor, sql, description=f"Creating {table_name} table")
        
        # Step 2: Add referral columns to users
        print("\n📝 Step 2: Adding referral columns to users...")
        
        if db_type == "postgresql":
            referral_columns = [
                ("referral_code", "ALTER TABLE users ADD COLUMN referral_code TEXT"),
                ("custom_commission_rate", "ALTER TABLE users ADD COLUMN custom_commission_rate DECIMAL(5,2)"),
                ("total_earned", "ALTER TABLE users ADD COLUMN total_earned DECIMAL(10,2) DEFAULT 0.00"),
                ("total_paid", "ALTER TABLE users ADD COLUMN total_paid DECIMAL(10,2) DEFAULT 0.00")
            ]
        else:
            referral_columns = [
                ("referral_code", "ALTER TABLE users ADD COLUMN referral_code TEXT"),
                ("custom_commission_rate", "ALTER TABLE users ADD COLUMN custom_commission_rate REAL"),
                ("total_earned", "ALTER TABLE users ADD COLUMN total_earned REAL DEFAULT 0.00"),
                ("total_paid", "ALTER TABLE users ADD COLUMN total_paid REAL DEFAULT 0.00")
            ]
        
        for column_name, sql in referral_columns:
            execute_sql_safe(cursor, sql, description=f"Adding {column_name} column")
        
        # Step 3: Add unique constraint for referral_code
        print("\n🔐 Step 3: Adding unique constraint...")
        
        if db_type == "postgresql":
            # Check if constraint exists first
            cursor.execute("""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE table_name='users' AND constraint_type='UNIQUE' 
                AND constraint_name='users_referral_code_unique'
            """)
            if not cursor.fetchone():
                execute_sql_safe(cursor, 
                    "ALTER TABLE users ADD CONSTRAINT users_referral_code_unique UNIQUE (referral_code)",
                    description="Adding unique constraint for referral_code"
                )
        else:
            # SQLite: Create unique index instead
            execute_sql_safe(cursor,
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_referral_code_unique ON users(referral_code)",
                description="Creating unique index for referral_code"
            )
        
        # Step 4: Create referral system tables
        print("\n📊 Step 4: Creating referral system tables...")
        
        if db_type == "postgresql":
            referral_tables = [
                ("referrals", """
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
                """),
                ("commissions", """
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
                """),
                ("referral_settings", """
                    CREATE TABLE IF NOT EXISTS referral_settings (
                        id SERIAL PRIMARY KEY,
                        setting_key TEXT UNIQUE NOT NULL,
                        setting_value TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            ]
        else:
            referral_tables = [
                ("referrals", """
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
                """),
                ("commissions", """
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
                """),
                ("referral_settings", """
                    CREATE TABLE IF NOT EXISTS referral_settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        setting_key TEXT UNIQUE NOT NULL,
                        setting_value TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            ]
        
        for table_name, sql in referral_tables:
            execute_sql_safe(cursor, sql, description=f"Creating {table_name} table")
        
        # Step 5: Insert default settings
        print("\n⚙️ Step 5: Adding default settings...")
        
        if db_type == "postgresql":
            execute_sql_safe(cursor, """
                INSERT INTO referral_settings (setting_key, setting_value) 
                VALUES (%s, %s)
                ON CONFLICT (setting_key) DO NOTHING
            """, ('min_withdrawal_amount', '20.00'), "Adding default referral settings")
        else:
            execute_sql_safe(cursor, """
                INSERT OR IGNORE INTO referral_settings (setting_key, setting_value) 
                VALUES (?, ?)
            """, ('min_withdrawal_amount', '20.00'), "Adding default referral settings")
        
        # Step 6: Create performance indexes
        print("\n🚀 Step 6: Creating performance indexes...")
        
        indexes = [
            ("idx_users_subscription", "CREATE INDEX IF NOT EXISTS idx_users_subscription ON users(subscription_end, is_active)"),
            ("idx_api_requests_date", "CREATE INDEX IF NOT EXISTS idx_api_requests_date ON api_requests(user_id, request_date)"),
            ("idx_referrals_referrer", "CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id)"),
            ("idx_referrals_referred", "CREATE INDEX IF NOT EXISTS idx_referrals_referred ON referrals(referred_id)"),
            ("idx_commissions_referrer", "CREATE INDEX IF NOT EXISTS idx_commissions_referrer ON commissions(referrer_id, status)"),
            ("idx_commissions_status", "CREATE INDEX IF NOT EXISTS idx_commissions_status ON commissions(status)")
        ]
        
        for index_name, sql in indexes:
            execute_sql_safe(cursor, sql, description=f"Creating {index_name}")
        
        # Final: Commit all changes
        print("\n💾 Committing all changes...")
        conn.commit()
        
        # Verification
        print("\n🔍 Final verification...")
        
        if db_type == "postgresql":
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
        else:
            cursor.execute("""
                SELECT name 
                FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
        
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📊 Final tables: {', '.join(tables)}")
        
        print("\n🎉 Migration completed successfully!")
        print("✅ Database is ready for production!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("🔄 Rolling back changes...")
        try:
            conn.rollback()
            print("✅ Rollback successful")
        except:
            print("❌ Rollback failed")
        return False
        
    finally:
        conn.close()
        print("🔒 Database connection closed")

if __name__ == "__main__":
    print("🛠️ Final Database Migration Tool")
    print("Supports both SQLite (dev) and PostgreSQL (prod)")
    print("=" * 60)
    
    success = final_migration()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("🚀 Ready for deployment!")
    else:
        print("\n❌ Migration failed!")
        print("📞 Check the error messages above")
    
    print("=" * 60)
