import os
import sys
sys.path.append('/app')

from database.operations import get_connection

def run_referral_migration():
    """اجرای Migration برای سیستم رفرال در Railway"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        print("🔄 Starting Referral System Migration on Railway...")
        
        # 1. اضافه کردن فیلدهای جدید به users
        print("📝 Adding new columns to users table...")
        
        migrations = [
            ("referral_code", "ALTER TABLE users ADD COLUMN referral_code TEXT"),
            ("custom_commission_rate", "ALTER TABLE users ADD COLUMN custom_commission_rate DECIMAL(5,2)"),
            ("total_earned", "ALTER TABLE users ADD COLUMN total_earned DECIMAL(10,2) DEFAULT 0.00"),
            ("total_paid", "ALTER TABLE users ADD COLUMN total_paid DECIMAL(10,2) DEFAULT 0.00")
        ]
        
        for column_name, sql in migrations:
            try:
                cursor.execute(sql)
                conn.commit()
                print(f"✅ Added {column_name} column")
            except Exception as e:
                conn.rollback()
                print(f"⚠️ {column_name} column: {str(e)[:100]}")
        
        # 2. اضافه کردن UNIQUE constraint برای referral_code
        try:
            cursor.execute("ALTER TABLE users ADD CONSTRAINT users_referral_code_unique UNIQUE (referral_code)")
            conn.commit()
            print("✅ Added unique constraint for referral_code")
        except Exception as e:
            conn.rollback()
            print(f"⚠️ Unique constraint: {str(e)[:100]}")
        
        # 3. ایجاد جداول جدید
        print("📊 Creating new tables...")
        
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
        conn.commit()
        print("✅ Created referrals table")
        
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
        conn.commit()
        print("✅ Created commissions table")
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referral_settings (
                id SERIAL PRIMARY KEY,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        print("✅ Created referral_settings table")
        
        # 4. مقادیر پیش‌فرض
        cursor.execute('''
            INSERT INTO referral_settings (setting_key, setting_value) 
            VALUES ('min_withdrawal_amount', '20.00')
            ON CONFLICT (setting_key) DO NOTHING
        ''')
        conn.commit()
        print("✅ Added default settings")
        
        print("🎉 Referral System Migration Completed Successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    run_referral_migration()
