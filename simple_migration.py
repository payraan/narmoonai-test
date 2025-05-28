#!/usr/bin/env python3
"""
Simple Migration Script - Direct Environment Variable Loading
"""
import os
import psycopg2

# Database URL از .env فایل
DATABASE_URL = None  # استفاده از SQLite

def simple_migration():
    """Migration ساده با URL مستقیم"""
    
    print("🔗 Connecting to database...")
    
    try:
        import sqlite3
        conn = sqlite3.connect('bot_database.db')
        conn.autocommit = False
        cursor = conn.cursor()
        
        print("✅ Connected successfully!")
        print("\n🔧 Starting migration...")
        
        # Step 1: Add columns to users table
        print("📝 Adding columns to users table...")
        
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS referral_code TEXT")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS custom_commission_rate DECIMAL(5,2)")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS total_earned DECIMAL(10,2) DEFAULT 0.00")
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS total_paid DECIMAL(10,2) DEFAULT 0.00")
            print("✅ Added columns to users table")
        except Exception as e:
            print(f"⚠️ Users columns: {e}")
        
        # Step 2: Add unique constraint
        print("🔐 Adding unique constraint...")
        try:
            cursor.execute("ALTER TABLE users ADD CONSTRAINT users_referral_code_unique UNIQUE (referral_code)")
            print("✅ Added unique constraint")
        except Exception as e:
            print(f"⚠️ Unique constraint: {e}")
        
        # Step 3: Create referrals table
        print("📊 Creating referrals table...")
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
            print(f"⚠️ Referrals table: {e}")
        
        # Step 4: Create commissions table
        print("💰 Creating commissions table...")
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
            print(f"⚠️ Commissions table: {e}")
        
        # Step 5: Create referral_settings table
        print("⚙️ Creating referral_settings table...")
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
            print(f"⚠️ Referral_settings table: {e}")
        
        # Step 6: Insert default settings
        print("📄 Adding default settings...")
        try:
            cursor.execute("""
                INSERT INTO referral_settings (setting_key, setting_value) 
                VALUES ('min_withdrawal_amount', '20.00')
                ON CONFLICT (setting_key) DO NOTHING
            """)
            print("✅ Added default settings")
        except Exception as e:
            print(f"⚠️ Default settings: {e}")
        
        # Commit all changes
        print("\n💾 Committing changes...")
        conn.commit()
        print("✅ All changes committed successfully!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        try:
            conn.rollback()
            print("🔄 Changes rolled back")
        except:
            pass
        return False
        
    finally:
        try:
            conn.close()
            print("🔒 Connection closed")
        except:
            pass

if __name__ == "__main__":
    print("🛠️ Simple Migration Tool")
    print("=" * 30)
    
    success = simple_migration()
    
    if success:
        print("\n🎉 Migration completed!")
        print("🚀 Ready to deploy!")
    else:
        print("\n❌ Migration failed!")
    
    print("=" * 30)
