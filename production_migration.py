#!/usr/bin/env python3
"""
Production Migration - اضافه کردن ستون‌های TNT به PostgreSQL
"""
import os
from database.operations import get_connection

def production_migration():
    """Migration برای production PostgreSQL"""
    
    print("🚀 Starting Production TNT Migration...")
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # بررسی نوع دیتابیس
        is_postgres = hasattr(conn, 'server_version')
        print(f"📊 Database Type: {'PostgreSQL' if is_postgres else 'SQLite'}")
        
        if not is_postgres:
            print("⚠️ This migration is for PostgreSQL only")
            return False
        
        # Step 1: اضافه کردن ستون‌های TNT به users
        print("\n📝 Adding TNT columns to users table...")
        
        tnt_columns = [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS tnt_plan_type TEXT DEFAULT 'FREE'",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS tnt_monthly_limit INTEGER DEFAULT 0",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS tnt_hourly_limit INTEGER DEFAULT 0", 
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS tnt_plan_start TIMESTAMP",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS tnt_plan_end TIMESTAMP"
        ]
        
        for sql in tnt_columns:
            try:
                cursor.execute(sql)
                print(f"✅ {sql.split()[-3]} column added")
            except Exception as e:
                print(f"⚠️ Column error: {str(e)[:50]}")
        
        # Step 2: ایجاد جدول tnt_usage_tracking
        print("\n📊 Creating TNT usage tracking table...")
        
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tnt_usage_tracking (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    usage_date DATE NOT NULL,
                    usage_hour INTEGER NOT NULL,
                    analysis_count INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    UNIQUE(user_id, usage_date, usage_hour)
                )
            """)
            print("✅ tnt_usage_tracking table created")
        except Exception as e:
            print(f"⚠️ Usage tracking table: {str(e)[:50]}")
        
        # Step 3: ایجاد جدول tnt_plans
        print("\n💎 Creating TNT plans table...")
        
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tnt_plans (
                    id SERIAL PRIMARY KEY,
                    plan_name TEXT UNIQUE NOT NULL,
                    plan_display_name TEXT NOT NULL,
                    price_usd DECIMAL(10,2) NOT NULL,
                    monthly_limit INTEGER NOT NULL,
                    hourly_limit INTEGER NOT NULL,
                    vip_access BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ tnt_plans table created")
        except Exception as e:
            print(f"⚠️ Plans table: {str(e)[:50]}")
        
        # Step 4: اضافه کردن پلن‌های پیش‌فرض
        print("\n🎯 Adding default TNT plans...")
        
        default_plans = [
            ('FREE', 'رایگان', 0.00, 0, 0, False),
            ('TNT_MINI', 'TNT MINI', 10.00, 60, 2, False),
            ('TNT_PLUS', 'TNT PLUS+', 18.00, 150, 4, False),
            ('TNT_MAX', 'TNT MAX', 39.00, 400, 8, True)
        ]
        
        for plan_name, display_name, price, monthly_limit, hourly_limit, vip_access in default_plans:
            try:
                cursor.execute("""
                    INSERT INTO tnt_plans (plan_name, plan_display_name, price_usd, monthly_limit, hourly_limit, vip_access)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (plan_name) DO UPDATE SET
                    plan_display_name = EXCLUDED.plan_display_name,
                    price_usd = EXCLUDED.price_usd,
                    monthly_limit = EXCLUDED.monthly_limit,
                    hourly_limit = EXCLUDED.hourly_limit,
                    vip_access = EXCLUDED.vip_access,
                    updated_at = CURRENT_TIMESTAMP
                """, (plan_name, display_name, price, monthly_limit, hourly_limit, vip_access))
                print(f"✅ Plan added: {display_name}")
            except Exception as e:
                print(f"⚠️ Plan {plan_name}: {str(e)[:50]}")
        
        # Step 5: ایجاد ایندکس‌ها
        print("\n🚀 Creating indexes...")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_tnt_plan ON users(tnt_plan_type, tnt_plan_end)",
            "CREATE INDEX IF NOT EXISTS idx_usage_tracking_user_date ON tnt_usage_tracking(user_id, usage_date)",
            "CREATE INDEX IF NOT EXISTS idx_usage_tracking_user_hour ON tnt_usage_tracking(user_id, usage_date, usage_hour)",
            "CREATE INDEX IF NOT EXISTS idx_tnt_plans_active ON tnt_plans(plan_name, is_active)"
        ]
        
        for sql in indexes:
            try:
                cursor.execute(sql)
                print(f"✅ Index created")
            except Exception as e:
                print(f"⚠️ Index: {str(e)[:50]}")
        
        # Commit
        print("\n💾 Committing changes...")
        conn.commit()
        
        # Verification
        print("\n🔍 Verification...")
        cursor.execute("SELECT COUNT(*) FROM tnt_plans WHERE is_active = true")
        plan_count = cursor.fetchone()[0]
        print(f"💎 Active TNT plans: {plan_count}")
        
        conn.close()
        
        print("\n🎉 Production TNT Migration completed!")
        print("✅ Railway deployment ready!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        try:
            conn.rollback()
            conn.close()
        except:
            pass
        return False

if __name__ == "__main__":
    print("🛠️ Production TNT Migration")
    print("=" * 40)
    
    success = production_migration()
    
    if success:
        print("\n✅ Migration successful!")
        print("🚀 TNT system ready!")
    else:
        print("\n❌ Migration failed!")
    
    print("=" * 40)
