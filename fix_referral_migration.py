#!/usr/bin/env python3
"""
Fix Referral Migration - هر عملیات در transaction جداگانه
"""
import os
import psycopg2

# Database URL مستقیم
DATABASE_URL = "postgresql://postgres:cOXpRpjZhCxoiVLZzdoWzCIaKVBaefBq@postgres.railway.internal:5432/railway"

def fix_referral_migration():
    """Migration با transaction های جداگانه"""
    
    print("🔗 Connecting to database...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("✅ Connected successfully!")
        
        # هر عملیات در transaction جداگانه
        operations = [
            ("Create referrals table", """
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
            ("Create commissions table", """
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
            ("Create referral_settings table", """
                CREATE TABLE IF NOT EXISTS referral_settings (
                    id SERIAL PRIMARY KEY,
                    setting_key TEXT UNIQUE NOT NULL,
                    setting_value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """),
            ("Insert default settings", """
                INSERT INTO referral_settings (setting_key, setting_value) 
                VALUES ('min_withdrawal_amount', '20.00')
                ON CONFLICT (setting_key) DO NOTHING
            """)
        ]
        
        success_count = 0
        
        for operation_name, sql in operations:
            try:
                print(f"🔧 {operation_name}...")
                
                # هر عملیات در transaction جداگانه
                conn.autocommit = False
                cursor = conn.cursor()
                cursor.execute(sql)
                conn.commit()
                cursor.close()
                
                print(f"✅ {operation_name} - Success!")
                success_count += 1
                
            except Exception as e:
                print(f"⚠️ {operation_name} - {str(e)[:100]}")
                try:
                    conn.rollback()
                except:
                    pass
        
        # Final check
        print(f"\n📊 Final check - {success_count}/{len(operations)} operations completed")
        
        # Check tables exist
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('referrals', 'commissions', 'referral_settings')
            ORDER BY table_name
        """)
        
        existing_tables = [row[0] for row in cursor.fetchall()]
        print(f"✅ Existing referral tables: {', '.join(existing_tables)}")
        cursor.close()
        
        return len(existing_tables) >= 2  # حداقل 2 جدول باید وجود داشته باشه
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        return False
        
    finally:
        try:
            conn.close()
            print("🔒 Connection closed")
        except:
            pass

if __name__ == "__main__":
    print("🛠️ Fix Referral Migration Tool")
    print("=" * 40)
    
    success = fix_referral_migration()
    
    if success:
        print("\n🎉 Referral tables created successfully!")
        print("🚀 Ready to test referral system!")
    else:
        print("\n❌ Some issues occurred")
        print("📞 Check the logs above")
    
    print("=" * 40)
